"""Shape A: deterministic workflow. Money and writes stay in host code."""

from __future__ import annotations

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import compute_compensation, get_claim_view, lookup_order, tool_cost
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
        run_id = make_run_id("workflow", claim_id, seed)
        trace = Trace(run_id)

        budget.add_tool(tool_cost())
        claim = get_claim_view(conn, claim_id)
        if not claim.get("found"):
            trace.add("error", {"reason": "unknown_claim"})
            return finish(conn, shape="workflow", claim_id=claim_id, seed=seed,
                          status="failed", proposal_amount=0, budget=budget,
                          trace=trace, error_reason="unknown_claim")

        if not claim.get("order_id"):
            trace.add("decision", {"status": "needs_info"})
            return finish(conn, shape="workflow", claim_id=claim_id, seed=seed,
                          status="needs_info", proposal_amount=0, budget=budget,
                          trace=trace, error_reason="missing_order_id")

        budget.add_tool(tool_cost())
        order_view = lookup_order(conn, claim["order_id"], claim["principal_id"])
        if not order_view.get("visible"):
            trace.add("order_lookup", {"visible": False, "reason": order_view.get("reason")})
            return finish(conn, shape="workflow", claim_id=claim_id, seed=seed,
                          status="escalated", proposal_amount=0, budget=budget,
                          trace=trace, error_reason=order_view.get("reason"))

        # Quote strictly from the allowlisted structured order view, never ticket text.
        budget.add_tool(tool_cost())
        quote = compute_compensation(conn, order_view["order"])
        proposal = int(quote["amount_vnd"])
        trace.add("quote", quote)
        if proposal <= 0:
            trace.add("decision", {"status": "denied"})
            return finish(conn, shape="workflow", claim_id=claim_id, seed=seed,
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
            return finish(conn, shape="workflow", claim_id=claim_id, seed=seed,
                          status=status, proposal_amount=proposal, budget=budget,
                          trace=trace, error_reason=outcome["reason"])
        trace.add("decision", {"status": "resolved"})
        return finish(conn, shape="workflow", claim_id=claim_id, seed=seed,
                      status="resolved", proposal_amount=proposal, budget=budget,
                      trace=trace)
    finally:
        conn.close()
