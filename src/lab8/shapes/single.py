"""Shape B: one bounded ReAct agent; all tools it can choose are read-only."""

from __future__ import annotations

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
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
        run_id = make_run_id("single", claim_id, seed)
        trace = Trace(run_id)

        # The initial context contains identifiers only. Ticket prose is untrusted
        # and is deliberately not copied into the trace or used to calculate money.
        state = {"stage": 0}

        def decide(observation: dict) -> dict:
            stage = state["stage"]
            complete(budget, seed=seed, purpose="single_step", prompt=f"stage={stage}; claim_id={claim_id}")
            if stage == 0:
                state["stage"] = 1
                return {"tool": "get_claim_view", "args": {"claim_id": claim_id}}
            last = observation.get("last_result") or {}
            if stage == 1:
                if not last.get("found"):
                    return {"final": {"status": "failed", "proposal_amount": 0, "error_reason": "unknown_claim"}}
                if not last.get("order_id"):
                    return {"final": {"status": "needs_info", "proposal_amount": 0, "error_reason": "missing_order_id"}}
                state["principal_id"] = last["principal_id"]
                state["order_id"] = last["order_id"]
                state["stage"] = 2
                return {"tool": "lookup_order", "args": {"order_id": last["order_id"], "principal_id": last["principal_id"]}}
            if stage == 2:
                if not last.get("visible"):
                    return {"final": {"status": "escalated", "proposal_amount": 0, "error_reason": last.get("reason")}}
                state["stage"] = 3
                return {"tool": "compute_compensation", "args": {"order": last["order"]}}
            quote = last
            amount = int(quote.get("amount_vnd", 0))
            return {"final": {
                "status": "resolved" if amount > 0 else "denied",
                "proposal_amount": amount,
                "error_reason": None if amount > 0 else quote.get("reason"),
            }}

        initial = {"claim": {"claim_id": claim_id}}
        outcome = run_react(conn, budget, observation=initial, decide=decide, max_steps=8)
        final = outcome["final"]
        status = final.get("status", "failed")
        proposal = int(final.get("proposal_amount", 0))
        quote_payload = (outcome.get("observation") or {}).get("last_result")
        if isinstance(quote_payload, dict) and "amount_vnd" in quote_payload:
            trace.add("quote", quote_payload)
        trace.add("agent", {"stopped": outcome["stopped"], "status": status})

        if status == "resolved":
            try:
                write_result = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
            except InjectedCrash:
                trace.add("crash", {"at": crash_at})
                trace.write()
                raise
            if not write_result["ok"]:
                status = "failed" if write_result.get("conflict") else "denied"
                final["error_reason"] = write_result["reason"]

        if status in {"needs_info", "escalated"}:
            trace.add("decision", {"status": status})
        elif status == "failed":
            trace.add("error", {"reason": final.get("error_reason") or "agent_failed"})
        elif status == "denied":
            trace.add("decision", {"status": status, "reason": final.get("error_reason") or "host_denied"})
        else:
            trace.add("decision", {"status": "resolved"})
        return finish(conn, shape="single", claim_id=claim_id, seed=seed,
                      status=status, proposal_amount=proposal, budget=budget,
                      trace=trace, error_reason=final.get("error_reason"))
    finally:
        conn.close()
