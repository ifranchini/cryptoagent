"""Snapshot GraphQL API — governance activity for crypto protocols."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 10
_SNAPSHOT_URL = "https://hub.snapshot.org/graphql"

# Maps token symbols to Snapshot space IDs.
# Solana uses Realms (not Snapshot), so SOL returns a stub note.
_TOKEN_SPACES: dict[str, list[str]] = {
    "ETH": ["ens.eth"],
    "ARB": ["arbitrumfoundation.eth"],
    "OP": ["opcollective.eth"],
    "AAVE": ["aave.eth"],
    "UNI": ["uniswapgovernance.eth"],
    "LINK": [],
    "MKR": ["makerdao.eth"],
    "PENDLE": ["pendle-finance.eth"],
    "GMX": ["gmx.eth"],
    "DYDX": ["dydxgov.eth"],
    "SNX": ["snxgov.eth"],
    "ENS": ["ens.eth"],
}

_PROPOSALS_QUERY = """\
query ($spaces: [String!]!) {
  proposals(
    first: 10
    where: { space_in: $spaces, state: "active" }
    orderBy: "created"
    orderDirection: desc
  ) {
    id
    title
    state
    choices
    scores_total
    votes
    start
    end
    space { id name }
  }
}
"""

_RECENT_PROPOSALS_QUERY = """\
query ($spaces: [String!]!) {
  proposals(
    first: 5
    where: { space_in: $spaces }
    orderBy: "created"
    orderDirection: desc
  ) {
    id
    title
    state
    votes
    scores_total
    space { id name }
  }
}
"""


def get_governance_activity(token: str) -> dict:
    """Fetch active and recent governance proposals for a token's Snapshot spaces.

    Solana tokens return a stub since Solana governance uses Realms, not Snapshot.
    Tokens without configured spaces return an informational note.
    """
    token_upper = token.upper()

    if token_upper == "SOL":
        return {
            "source": "snapshot",
            "token": token_upper,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "SOL governance uses Realms (realms.today), not Snapshot.",
            "active_proposals": 0,
            "proposals": [],
        }

    spaces = _TOKEN_SPACES.get(token_upper, [])
    if not spaces:
        return {
            "source": "snapshot",
            "token": token_upper,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": f"No Snapshot spaces configured for {token_upper}",
            "active_proposals": 0,
            "proposals": [],
        }

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            # Fetch active proposals
            active_resp = client.post(
                _SNAPSHOT_URL,
                json={"query": _PROPOSALS_QUERY, "variables": {"spaces": spaces}},
            )
            active_resp.raise_for_status()
            active_data = active_resp.json()
            active_proposals = active_data.get("data", {}).get("proposals", [])

            # Fetch recent proposals (any state) for context
            recent_resp = client.post(
                _SNAPSHOT_URL,
                json={
                    "query": _RECENT_PROPOSALS_QUERY,
                    "variables": {"spaces": spaces},
                },
            )
            recent_resp.raise_for_status()
            recent_data = recent_resp.json()
            recent_proposals = recent_data.get("data", {}).get("proposals", [])

        active_list = [
            {
                "title": p.get("title", ""),
                "state": p.get("state", ""),
                "votes": p.get("votes", 0),
                "space": p.get("space", {}).get("name", ""),
            }
            for p in active_proposals
        ]

        recent_list = [
            {
                "title": p.get("title", ""),
                "state": p.get("state", ""),
                "votes": p.get("votes", 0),
                "space": p.get("space", {}).get("name", ""),
            }
            for p in recent_proposals
        ]

        return {
            "source": "snapshot",
            "token": token_upper,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_proposals": len(active_list),
            "proposals": active_list,
            "recent_proposals": recent_list,
        }
    except Exception as e:
        logger.warning("Snapshot governance fetch failed for %s: %s", token_upper, e)
        return {
            "source": "error",
            "token": token_upper,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": str(e),
            "active_proposals": 0,
            "proposals": [],
        }
