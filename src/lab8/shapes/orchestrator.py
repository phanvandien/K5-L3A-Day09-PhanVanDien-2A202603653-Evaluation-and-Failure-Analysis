"""Shape C: orchestrator with a sanitized, read-only investigator handoff."""

from __future__ import annotations

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        budget = Budget()
        run_id = make_run_id("orchestrator", claim_id, seed)
        trace = Trace(run_id)
        budget.add_tool(tool_cost())
        claim = get_claim_view(conn, claim_id)
        if not claim.get("found"):
            trace.add("error", {"reason": "unknown_claim"})
            return finish(conn, shape="orchestrator", claim_id=claim_id, seed=seed,
                          status="failed", proposal_amount=0, budget=budget,
                          trace=trace, error_reason="unknown_claim")
        if not claim.get("order_id"):
            trace.add("decision", {"status": "needs_info"})
            return finish(conn, shape="orchestrator", claim_id=claim_id, seed=seed,
                          status="needs_info", proposal_amount=0, budget=budget,
                          trace=trace, error_reason="missing_order_id")

        # The parent only forwards the claim identifier and explicitly allowed
        # read tools. Raw claim context, ticket text, headers, and secrets stay local.
        handoff = make_handoff(
            request_id=f"REQ-{claim_id}",
            claim_id=claim_id,
            task="check_order_and_current_compensation",
            facts={},
            allowed_tools=[
                "lookup_order",
                "lookup_policy",
                "lookup_refund_history",
                "compute_compensation",
            ],
        )
        trace.add("handoff", safe_dump(handoff))
        complete(budget, seed=seed, purpose="orchestrator", prompt="delegate read-only order and policy investigation")
        investigation = run_readonly_investigators(
            conn, budget, handoff, principal_id=claim["principal_id"]
        )
        tools = investigation.get("tools", {})
        order_view = tools.get("lookup_order", {})
        # Trace only the allowlisted business order view, never parent context.
        if order_view.get("visible"):
            trace.add("investigator", {
                "order": order_view["order"],
                "policy_count": len((tools.get("lookup_policy") or {}).get("policies") or []),
                "refund_history": tools.get("lookup_refund_history"),
            })
        else:
            trace.add("investigator", {"visible": False, "reason": order_view.get("reason")})
            return finish(conn, shape="orchestrator", claim_id=claim_id, seed=seed,
                          status="escalated", proposal_amount=0, budget=budget,
                          trace=trace, error_reason=order_view.get("reason"))

        quote = tools.get("compute_compensation")
        if not isinstance(quote, dict):
            trace.add("error", {"reason": "investigator_missing_quote"})
            return finish(conn, shape="orchestrator", claim_id=claim_id, seed=seed,
                          status="failed", proposal_amount=0, budget=budget,
                          trace=trace, error_reason="investigator_missing_quote")
        proposal = int(quote["amount_vnd"])
        trace.add("quote", quote)
        complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")
        if proposal <= 0:
            trace.add("decision", {"status": "denied"})
            return finish(conn, shape="orchestrator", claim_id=claim_id, seed=seed,
                          status="denied", proposal_amount=0, budget=budget,
                          trace=trace, error_reason=quote.get("reason"))

        try:
            outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
        except InjectedCrash:
            trace.add("crash", {"at": crash_at})
            trace.write()
            raise
        if not outcome["ok"]:
            status = "failed" if outcome.get("conflict") else "denied"
            trace.add("decision", {"status": status, "reason": outcome["reason"]})
            return finish(conn, shape="orchestrator", claim_id=claim_id, seed=seed,
                          status=status, proposal_amount=proposal, budget=budget,
                          trace=trace, error_reason=outcome["reason"])
        trace.add("decision", {"status": "resolved"})
        return finish(conn, shape="orchestrator", claim_id=claim_id, seed=seed,
                      status="resolved", proposal_amount=proposal, budget=budget,
                      trace=trace)
    finally:
        conn.close()
