"""Pure screening helpers."""

from __future__ import annotations

from typing import Sequence


def rank_members(
    members: Sequence[dict[str, object]],
    *,
    limit: int,
    descending: bool = True,
) -> list[dict[str, object]]:
    if limit < 0:
        raise ValueError("limit must be non-negative")
    qualified = [member for member in members if member.get("change_percent") is not None]
    return sorted(
        qualified,
        key=lambda member: float(member.get("change_percent", 0.0)),
        reverse=descending,
    )[:limit]

