"""FastAPI sidecar for triggering CryptoAgent pipeline runs from the dashboard."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from cryptoagent.config import AgentConfig
from cryptoagent.graph.builder import TradingGraph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CryptoAgent Sidecar")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for tracking runs
_run_state = {
    "running": False,
    "last_started": None,
    "last_result": None,
    "error": None,
}


class RunRequest(BaseModel):
    token: str = "SOL"
    cycles: int = 1


class RunResponse(BaseModel):
    status: str
    token: str
    cycles: int


def _run_pipeline(token: str, cycles: int) -> None:
    """Execute the trading pipeline synchronously."""
    try:
        _run_state["running"] = True
        _run_state["error"] = None
        _run_state["last_started"] = datetime.now(timezone.utc).isoformat()

        config = AgentConfig()
        config_overrides = {"target_token": token}
        effective_config = config.model_copy(update=config_overrides)
        graph = TradingGraph(effective_config)
        result = graph.run(token=token, cycles=cycles)

        _run_state["last_result"] = {
            "token": token,
            "cycles": cycles,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "action": result.get("brain_decision", {}).get("action", "unknown")
            if isinstance(result, dict)
            else "completed",
        }
        logger.info("Pipeline completed for %s (%d cycles)", token, cycles)
    except Exception as e:
        logger.exception("Pipeline failed")
        _run_state["error"] = str(e)
    finally:
        _run_state["running"] = False


@app.post("/run", response_model=RunResponse)
async def trigger_run(req: RunRequest):
    """Trigger a pipeline run in the background."""
    if _run_state["running"]:
        return RunResponse(
            status="already_running", token=req.token, cycles=req.cycles
        )

    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _run_pipeline, req.token, req.cycles)

    return RunResponse(status="started", token=req.token, cycles=req.cycles)


@app.get("/status")
async def get_status():
    """Get current run status."""
    return {
        "running": _run_state["running"],
        "last_started": _run_state["last_started"],
        "last_result": _run_state["last_result"],
        "error": _run_state["error"],
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
