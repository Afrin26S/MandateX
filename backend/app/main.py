"""
MandateX API.

Every route that touches money goes through MandateEngine first. Routes
never call Razorpay directly without a passing decision from the engine.

Run from the backend/ folder with the venv active:
    uvicorn app.main:app --reload --port 5000

Then open http://127.0.0.1:5000/docs for an interactive test UI.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .mandate_engine import MandateEngine
from .audit_log import AuditLog
from .catalog import CATALOG, find_product, search_catalog
from .mandate_config import MANDATE
from .razorpay_client import create_test_order
from .dashboard import DASHBOARD_HTML

app = FastAPI(title="MandateX")

# In-memory for the demo. A real deployment would scope these per user/session.
engine = MandateEngine()
log = AuditLog()


class PurchaseRequest(BaseModel):
    product_id: str
    quantity: int = 1


class ActionAttemptRequest(BaseModel):
    action: str
    context: str = ""


@app.get("/catalog")
def get_catalog():
    return CATALOG


@app.get("/catalog/search")
def search(q: str):
    results = search_catalog(q)
    log.log("catalog_lookup", {"query": q, "results_count": len(results)})
    return results


@app.post("/purchase")
def purchase(req: PurchaseRequest):
    """The core money-moving route. Scenario 1 and 2 both hit this."""
    product = find_product(req.product_id)
    decision = engine.check_purchase(req.product_id, req.quantity)

    log.log(
        "authorization_check",
        {
            "product": product["name"] if product else req.product_id,
            "price": product["price"] if product else None,
            "result": "APPROVED" if decision.allowed else "BLOCKED",
            "reason": decision.reason,
        },
    )

    if not decision.allowed:
        return {"success": False, "reason": decision.reason}

    total = product["price"] * req.quantity

    # Reserved test SKU: deterministically simulates a payment decline so we
    # can demo graceful failure handling without a real card-entry flow.
    # Mandate approval and payment success are different things — this SKU
    # proves the agent never conflates "approved" with "paid".
    if req.product_id == "P010":
        log.log(
            "payment",
            {
                "status": "PAYMENT_FAILED",
                "amount": total,
                "reason": "Simulated decline (test SKU) \u2014 payment authorization failed after mandate approval.",
            },
        )
        return {
            "success": False,
            "payment_status": "failed",
            "reason": "Mandate approved this purchase, but the payment itself failed. No order was marked as paid.",
        }

    try:
        order = create_test_order(total, receipt=f"order_{req.product_id}")
    except Exception as e:
        log.log("payment_error", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

    log.log("payment", {"status": "order_created", "razorpay_order_id": order["id"], "amount": total})
    engine.record_spend(total)

    return {"success": True, "needs_confirmation": decision.needs_confirmation, "razorpay_order": order}


@app.post("/action-attempt")
def action_attempt(req: ActionAttemptRequest):
    """Scenario 3 hits this — the agent (possibly manipulated by injected text)
    tries a non-purchase action like 'refund', and the engine decides, not the LLM."""
    decision = engine.check_action(req.action)
    log.log("agent_intent", {"context": req.context, "requested_action": req.action})
    log.log(
        "authorization_check",
        {"action": req.action, "result": "APPROVED" if decision.allowed else "BLOCKED", "reason": decision.reason},
    )
    return {"allowed": decision.allowed, "reason": decision.reason}


@app.get("/audit-log")
def get_audit_log():
    return log.entries


@app.get("/mandate")
def get_mandate():
    return MANDATE


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML