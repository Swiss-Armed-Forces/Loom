# Searching, indexing and the AI features

## What happens to a document

1. The file lands in object storage — from a USB stick, or uploaded through the web UI.
2. The crawler notices it and schedules work.
3. A worker extracts the content and metadata with Apache Tika, runs OCR on images and scanned
    PDFs, and renders what needs rendering.
4. The result is indexed into Elasticsearch.
5. The web UI and the API query that index.

Nothing is searchable until step 4 finishes. A file that was just added and cannot be found is
almost always still in the pipeline rather than broken — give it time before treating it as a
fault.

## Searching

Search is full-text over the extracted content **and** the extracted metadata, so a scanned image
with no text layer becomes searchable once OCR has run on it. The web UI at
`http://frontend.loom` is the way in; the same queries are available through `/v1/files` on the
API — which answers with file *ids* and sort cursors, nothing else, so a hit needs
`GET /v1/files/{file_id}` to become a name. When the question is a filename,
`/v1/files/search_by_filename` answers it directly.

Beyond plain text search, the UI offers filtering by tags and by extracted metadata, browsing the
file tree, and per-file previews and thumbnails.

## The AI features

These exist only on a box that deploys Ollama — which means a box with a GPU. If the AI parts of
the UI are missing or fail, the first question is whether this image has them at all, not what is
broken.

- **Summarisation** — a generated summary per document.
- **Translation** — documents translated into another language.
- **Image description** — generated descriptions of images, which also makes them searchable.
- **The RAG chatbot** — ask questions across the indexed corpus. It retrieves relevant documents
  and answers from them, so its answers are grounded in what has actually been ingested.

All of it runs locally against the box's own Ollama. Nothing is sent anywhere.

The depth is in `/home/loom/loom/Documentation/ai.md` — `## RAG Pipeline` for how retrieval works,
`## Available Tools Reference` for what the chatbot can do, and `## Architecture Overview` for how
the pieces fit.

## When something is not indexed

In order:

1. Has enough time passed? OCR on a large scanned PDF is slow.
2. Is the file type supported? Tika handles most things, but not everything.
3. Is the pipeline healthy? That is an appliance question — queue depths at `http://rabbit.loom` in a browser,
    or `/v1/queues` on the API. If tasks are piling up in the `graveyard`, `dead` or `abyss` queues,
    they are failing repeatedly and the worker logs have the reason.

Step 3 is where this stops being a usage question. Diagnosing the pipeline itself is the
`loom-appliance` skill.
