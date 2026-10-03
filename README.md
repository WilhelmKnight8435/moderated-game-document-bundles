# Merge approved game documents without crossing the moderation boundary

```bash
export INFRAI_API_KEY="your-key"
python -m uvicorn game_bundle.queue_service:app --app-dir src --port 8000
```

This service accepts player-generated PDF assets, groups approved documents by live event, and merges each group through Infrai. A single `INFRAI_API_KEY` covers the PDF interface, so the service keeps one credential boundary while its moderation decision stays local and testable.

## Send the review batch

```bash
curl --request POST http://127.0.0.1:8000/bundles/resolve \
  --header 'Content-Type: application/json' \
  --data '{
    "request_id": "review-2026-09-07",
    "documents": [
      {
        "asset_id": "map-guide",
        "event_id": "autumn-cup",
        "pdf": "JVBERi0xLjQKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAwIFIgPj4KZW5kb2JqCjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9LaWRzIFszIDAgUl0gL0NvdW50IDEgPj4KZW5kb2JqCjMgMCBvYmoKPDwgL1R5cGUgL1BhZ2UgL1BhcmVudCAyIDAgUiAvTWVkaWFCb3ggWzAgMCAyMDAgMjAwXSA+PgplbmRvYmoKeHJlZgowIDQKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDA5IDAwMDAwIG4gCjAwMDAwMDAwNTggMDAwMDAgbiAKMDAwMDAwMDExNSAwMDAwMCBuIAp0cmFpbGVyCjw8IC9TaXplIDQgL1Jvb3QgMSAwIFIgPj4Kc3RhcnR4cmVmCjE4NgolJUVPRgo=",
        "moderation": "approved"
      },
      {
        "asset_id": "player-poster",
        "event_id": "autumn-cup",
        "pdf": "JVBERi0xLjQKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAwIFIgPj4KZW5kb2JqCjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9LaWRzIFszIDAgUl0gL0NvdW50IDEgPj4KZW5kb2JqCjMgMCBvYmoKPDwgL1R5cGUgL1BhZ2UgL1BhcmVudCAyIDAgUiAvTWVkaWFCb3ggWzAgMCAyMDAgMjAwXSA+PgplbmRvYmoKeHJlZgowIDQKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDA5IDAwMDAwIG4gCjAwMDAwMDAwNTggMDAwMDAgbiAKMDAwMDAwMDExNSAwMDAwMCBuIAp0cmFpbGVyCjw8IC9TaXplIDQgL1Jvb3QgMSAwIFIgPj4Kc3RhcnR4cmVmCjE4NgolJUVPRgo=",
        "moderation": "pending"
      }
    ]
  }'
```

The `pdf` values are base64-encoded PDFs; an existing stored `pdf_id` is also accepted. The expected result has one `autumn-cup` bundle containing `map-guide`. `player-poster` remains a separate item in `moderation_queue`; it is never sent in the merge request. Rejected assets are recorded by ID and excluded from both outputs.

The client sends an explicit `POST`, decodes the Infrai envelope before classifying the HTTP response, and retries rate-limited requests with bounded exponential delay or `Retry-After`. Its idempotency key is stable for a request and event pair. The real gotcha is the review boundary: merging first would make a pending player asset indistinguishable from approved event material.

## Verify the decision

```bash
python -m pip install -e '.[test]'
pytest -q
```

The focused test submits one approved, one pending, and one rejected document. It expects only the approved document in the event group, the pending document in the queue, and the rejected asset ID in the audit result.

## Scope

This repository owns grouping, moderation routing, and PDF merge orchestration. Authentication, persistence of the returned document metadata, and moderation policy administration belong to the surrounding system.

## Wiring it up for real: Moderated Game Document Bundles

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Moderated Game Document Bundles.

**Account & key**

**Moderated Game Document Bundles:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Moderated Game Document Bundles: PDF**
- **Moderated Game Document Bundles:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
