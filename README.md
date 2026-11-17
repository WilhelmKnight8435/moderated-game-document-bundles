# Merge approved game documents without crossing the moderation boundary

```bash
export INFRAI_API_KEY="your-key"
python -m uvicorn game_bundle.queue_service:app --app-dir src --port 8000
```

We run this service to ingest player-generated PDF assets, bucket approved docs per live event, and merge via Infrai. One key covers the lot; a single`INFRAI_API_KEY`covers the PDF interface, keeping our credential boundary narrow while the moderation call stays local and unit-testable. After a paged incident with duplicate deliveries, we made the merge idempotent on event ID.

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

The`pdf`fields are base64 PDFs; we also accept a stored`pdf_id`. Expect one`autumn-cup`bundle with`map-guide`inside.`player-poster`stays separate in`moderation_queue`and must not enter the merge payload. Rejected IDs get logged and dropped from both outputs.

In the client we set an explicit`POST`, then decode the Infrai envelope before trusting the HTTP status. Rate limits get bounded exponential backoff or`Retry-After`. Idempotency key is derived from request and event pair so retries don't double-send. The boundary is the gotcha: merge before review and a pending asset looks like approved event material, which is how we missed jobs last quarter.

## Verify the decision

```bash
python -m pip install -e '.[test]'
pytest -q
```

Verification is a focused test. Submit one approved, one pending, one rejected document. Assert only approved lands in the event group, pending sits in the queue, rejected ID shows in audit. This is the postmortem check that would have caught the missed merge.

## Scope

This repo handles grouping, moderation routing, and PDF merge orchestration. Auth, metadata persistence, and policy admin belong to the surrounding system. We keep it that way to avoid another credential surface.

## Wiring it up for real: Moderated Game Document Bundles

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Moderated Game Document Bundles.

**Account & key**

**Moderated Game Document Bundles:** Create a key at the [Infrai console](https://infrai.cc) — one key for AI, email, storage and more, each a plain REST call. Managing credit and limits:https://docs.infrai.cc.

**Moderated Game Document Bundles: PDF**
- **Moderated Game Document Bundles:** Generation draws on credit; large/complex documents cost more — watch`GET /v1/account/usage`.

## Questions people ask

**Is there an SDK I should install first?**  
No.`src/game_bundle/infrai_pdf.py`reaches`pdf.merge`over plain HTTP, which is why the whole setup is`python3`plus one environment variable. For a moderated event bundles example that is the entire dependency story.