from game_bundle.moderation_bundle import (
    BundleRequest,
    ModerationState,
    PlayerDocument,
    partition_documents,
)


def test_only_approved_documents_enter_event_bundles() -> None:
    request = BundleRequest(
        request_id="review-2026-09-07",
        documents=[
            PlayerDocument(
                asset_id="map-guide",
                event_id="autumn-cup",
                pdf="https://assets.example/map-guide.pdf",
                moderation=ModerationState.APPROVED,
            ),
            PlayerDocument(
                asset_id="player-poster",
                event_id="autumn-cup",
                pdf="https://assets.example/player-poster.pdf",
                moderation=ModerationState.PENDING,
            ),
            PlayerDocument(
                asset_id="removed-chat-log",
                event_id="autumn-cup",
                pdf="https://assets.example/chat-log.pdf",
                moderation=ModerationState.REJECTED,
            ),
        ],
    )

    approved, queued, rejected = partition_documents(request)

    assert [item.asset_id for item in approved["autumn-cup"]] == ["map-guide"]
    assert [item.asset_id for item in queued] == ["player-poster"]
    assert rejected == ["removed-chat-log"]
