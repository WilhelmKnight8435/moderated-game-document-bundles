from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .infrai_pdf import InfraiPdfClient


class ModerationState(StrEnum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"


@dataclass(frozen=True)
class PlayerDocument:
    asset_id: str
    event_id: str
    pdf: str
    moderation: ModerationState


@dataclass(frozen=True)
class BundleRequest:
    request_id: str
    documents: list[PlayerDocument]


@dataclass(frozen=True)
class EventBundle:
    event_id: str
    asset_ids: list[str]
    document: dict[str, object]


@dataclass(frozen=True)
class BundleResult:
    merged: list[EventBundle]
    moderation_queue: list[PlayerDocument]
    rejected_asset_ids: list[str]


def partition_documents(
    request: BundleRequest,
) -> tuple[dict[str, list[PlayerDocument]], list[PlayerDocument], list[str]]:
    approved: dict[str, list[PlayerDocument]] = defaultdict(list)
    queued: list[PlayerDocument] = []
    rejected: list[str] = []

    for document in request.documents:
        if document.moderation == ModerationState.APPROVED:
            approved[document.event_id].append(document)
        elif document.moderation == ModerationState.PENDING:
            queued.append(document)
        else:
            rejected.append(document.asset_id)
    return dict(approved), queued, rejected


async def build_event_bundles(
    request: BundleRequest, client: "InfraiPdfClient"
) -> BundleResult:
    approved, queued, rejected = partition_documents(request)
    merged: list[EventBundle] = []

    for event_id in sorted(approved):
        documents = approved[event_id]
        digest = hashlib.sha256(
            f"{request.request_id}:{event_id}".encode("utf-8")
        ).hexdigest()
        output = await client.merge([item.pdf for item in documents], digest)
        merged.append(
            EventBundle(
                event_id=event_id,
                asset_ids=[item.asset_id for item in documents],
                document=output,
            )
        )

    return BundleResult(
        merged=merged,
        moderation_queue=queued,
        rejected_asset_ids=rejected,
    )
