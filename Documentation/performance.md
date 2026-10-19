# Performance

How to find out what Loom is spending time on.

For the frontend specifically — profiling the running app, and measuring what the result list
does under a real corpus — see [Frontend debugging](frontend-debugging.md).

## Finding out which request is slow

Every API response carries a `Server-Timing` header reporting how long the API spent on it, under
the route template that served it:

```text
Server-Timing: total;dur=182.4;desc="/v1/files/{file_id}/preview"
```

Browser devtools shows this on the Timing tab of each request in the network panel, which is enough
to tell a slow search apart from slow document previews without reaching for the pod logs. The
route template is reported rather than the path, so every preview is one endpoint rather than one
entry per file. The header is exposed through CORS, so a frontend served from another origin can
read it too.

The header is added by `backend/api/api/server_timing.py` and exposed in
`backend/api/api/api.py`.
