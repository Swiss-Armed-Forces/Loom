import { http, HttpResponse } from "msw";

import {
    GetFilePreviewResponseToJSON,
    GetFileResponseToJSON,
    type GetFilesResponse,
    GetFilesResponseToJSON,
    GroupedHistogramStatisticsModelToJSON,
    TermsStatisticsModelToJSON,
} from "@app/api/generated";

import { DemoQueryError, valuesForField } from "../query";
import {
    DEMO_THUMBNAIL_FILE_ID,
    addTags,
    getDocument,
    getRenderedAssetUrl,
    getTags,
    removeTag,
    removeTagGlobally,
    scheduleDemoTimeout,
    scheduleTask,
    searchDocuments,
    updateDocument,
    type DemoDocument,
    type DemoTask,
} from "../repository";

import { sendToChannel } from "./channels";
import {
    documentDetail,
    documentPreview,
    treeChildren,
    treeSpine,
} from "./documents";
import {
    empty,
    error,
    json,
    objectValue,
    parseBody,
    queryFromUrl,
    stringArrayValue,
    stringValue,
} from "./shared";
import {
    AVAILABLE_HISTOGRAM_STATS,
    AVAILABLE_TERMS_STATS,
    groupedHistogramStatistics,
    termsStatistics,
} from "./statistics";

const TREE_PAGE_SIZE = 3;

const safeSearch = (
    query: string,
):
    | { ok: true; documents: DemoDocument[] }
    | { ok: false; response: Response } => {
    try {
        return { ok: true, documents: searchDocuments(query) };
    } catch (reason) {
        const detail =
            reason instanceof DemoQueryError
                ? reason.message
                : "Invalid demo search query";
        return { ok: false, response: error(detail, 400) };
    }
};

const paginateTree = <Node extends { full_path: string }>(
    nodes: Node[],
    after: string | null,
): { nodes: Node[]; next_page_cursor?: string } => {
    const cursorIndex = after
        ? nodes.findIndex((node) => node.full_path === after)
        : -1;
    if (after && cursorIndex < 0) return { nodes: [] };
    const page = nodes.slice(cursorIndex + 1, cursorIndex + 1 + TREE_PAGE_SIZE);
    const hasMore = cursorIndex + 1 + page.length < nodes.length;
    return {
        nodes: page,
        next_page_cursor: hasMore ? page.at(-1)?.full_path : undefined,
    };
};

const sortValue = (document: DemoDocument, field: string): string | number => {
    if (field === "size") return document.size;
    return valuesForField(document, field)[0] ?? document.uploadedAt;
};

const compareValues = (
    left: string | number,
    right: string | number,
): number =>
    typeof left === "number" && typeof right === "number"
        ? left - right
        : String(left).localeCompare(String(right));

const updateValues = (
    body: Record<string, unknown>,
):
    | {
          ok: true;
          value: { flagged?: boolean; hidden?: boolean; seen?: boolean };
      }
    | { ok: false } => {
    const value: { flagged?: boolean; hidden?: boolean; seen?: boolean } = {};
    for (const field of ["flagged", "hidden", "seen"] as const) {
        if (body[field] === undefined) continue;
        if (typeof body[field] !== "boolean") return { ok: false };
        value[field] = body[field];
    }
    return { ok: true, value };
};

const fileIdFromRequest = (request: Request, expression: RegExp): string => {
    const match = new URL(request.url).pathname.match(expression);
    return decodeURIComponent(match?.[1] ?? "");
};

const queryHandler = http.post(/\/api\/v1\/files\/query$/, () =>
    json({ query_id: crypto.randomUUID(), keep_alive: "30m" }),
);

const countHandler = http.get(/\/api\/v1\/files\/count$/, ({ request }) => {
    const result = safeSearch(queryFromUrl(new URL(request.url)));
    return result.ok
        ? json({ total_files: result.documents.length })
        : result.response;
});

const tagsListHandler = http.get(/\/api\/v1\/files\/tags$/, () =>
    json(getTags()),
);

const tagsBulkAddHandler = http.post(
    /\/api\/v1\/files\/tags$/,
    async ({ request }) => {
        const parsed = await parseBody(request);
        if (!parsed.ok) return parsed.response;
        const tags = stringArrayValue(parsed.value.tags);
        const query = objectValue(parsed.value.query);
        if (!tags || !query || typeof query.search_string !== "string")
            return error("query.search_string and tags are required", 422);
        const result = safeSearch(query.search_string);
        if (!result.ok) return result.response;
        result.documents.forEach((document) => addTags(document.id, tags));
        return empty(202);
    },
);

const globalTagDeleteHandler = http.delete(
    /\/api\/v1\/files\/tags\/([^/]+)$/,
    ({ request }) => {
        removeTagGlobally(fileIdFromRequest(request, /\/tags\/([^/]+)$/));
        return empty(202);
    },
);

const availableTermsHandler = http.get(/\/api\/v1\/files\/stats\/terms$/, () =>
    json(AVAILABLE_TERMS_STATS),
);

const availableHistogramHandler = http.get(
    /\/api\/v1\/files\/stats\/histogram$/,
    () => json(AVAILABLE_HISTOGRAM_STATS),
);

const termsHandler = http.get(
    /\/api\/v1\/files\/stats\/terms\/([^/]+)$/,
    ({ request }) => {
        const url = new URL(request.url);
        const result = safeSearch(queryFromUrl(url));
        if (!result.ok) return result.response;
        const stat = fileIdFromRequest(request, /\/stats\/terms\/([^/]+)$/);
        if (!AVAILABLE_TERMS_STATS.some((item) => item.id === stat))
            return error(`Unsupported terms statistic: ${stat}`, 422);
        const requestedSize = Number(url.searchParams.get("size") ?? 10);
        const size = Number.isFinite(requestedSize)
            ? Math.max(1, Math.min(100, requestedSize))
            : 10;
        return json(
            TermsStatisticsModelToJSON(
                termsStatistics(result.documents, stat, size),
            ),
        );
    },
);

const histogramHandler = http.get(
    /\/api\/v1\/files\/stats\/histogram\/([^/]+)\/grouped\/([^/]+)$/,
    ({ request }) => {
        const url = new URL(request.url);
        const result = safeSearch(queryFromUrl(url));
        if (!result.ok) return result.response;
        const match = url.pathname.match(
            /\/stats\/histogram\/([^/]+)\/grouped\/([^/]+)$/,
        );
        const stat = decodeURIComponent(match?.[1] ?? "");
        const groupBy = decodeURIComponent(match?.[2] ?? "");
        if (!AVAILABLE_HISTOGRAM_STATS.some((item) => item.id === stat))
            return error(`Unsupported histogram statistic: ${stat}`, 422);
        if (!AVAILABLE_TERMS_STATS.some((item) => item.id === groupBy))
            return error(`Unsupported histogram grouping: ${groupBy}`, 422);
        return json(
            GroupedHistogramStatisticsModelToJSON(
                groupedHistogramStatistics(result.documents, stat, groupBy),
            ),
        );
    },
);

const treeHandler = http.get(/\/api\/v1\/files\/tree$/, ({ request }) => {
    const url = new URL(request.url);
    const result = safeSearch(queryFromUrl(url));
    if (!result.ok) return result.response;
    return json(
        paginateTree(
            treeChildren(result.documents, url.searchParams.get("node_path")),
            url.searchParams.get("after"),
        ),
    );
});

const treeSpineHandler = http.get(
    /\/api\/v1\/files\/tree\/spine$/,
    ({ request }) => {
        const url = new URL(request.url);
        const result = safeSearch(queryFromUrl(url));
        return result.ok
            ? json({
                  nodes: treeSpine(
                      result.documents,
                      url.searchParams.get("full_path"),
                  ),
              })
            : result.response;
    },
);

const filenameHandler = http.get(
    /\/api\/v1\/files\/search_by_filename$/,
    ({ request }) => {
        const url = new URL(request.url);
        const result = safeSearch(queryFromUrl(url));
        if (!result.ok) return result.response;
        const filename = url.searchParams.get("filename")?.toLowerCase();
        if (filename === undefined) return error("filename is required", 422);
        const nodes = result.documents
            .filter((document) =>
                document.name.toLowerCase().includes(filename),
            )
            .map((document) => ({
                full_path: document.path,
                file_count: 1,
                file_id: document.id,
            }));
        return json(paginateTree(nodes, url.searchParams.get("after")));
    },
);

const filesListHandler = http.get(/\/api\/v1\/files$/, ({ request }) => {
    const url = new URL(request.url);
    const result = safeSearch(queryFromUrl(url));
    if (!result.ok) return result.response;
    const sortDirection = url.searchParams.get("sort_direction") ?? "desc";
    const sortByField =
        url.searchParams.get("sort_by_field") ?? "uploaded_datetime";
    const requestedSize = Number(url.searchParams.get("page_size") ?? 25);
    if (!Number.isInteger(requestedSize) || requestedSize < 1)
        return error("page_size must be a positive integer", 422);
    const pageSize = Math.min(requestedSize, 100);
    const matches = [...result.documents].sort((left, right) => {
        const comparison = compareValues(
            sortValue(left, sortByField),
            sortValue(right, sortByField),
        );
        const directed = sortDirection === "asc" ? comparison : -comparison;
        return directed || left.id.localeCompare(right.id);
    });
    const cursorId = url.searchParams.getAll("sort_id").at(-1);
    const cursorIndex = cursorId
        ? matches.findIndex((document) => document.id === cursorId)
        : -1;
    if (cursorId && cursorIndex < 0)
        return error("Invalid sort_id cursor", 400);
    const page = matches.slice(cursorIndex + 1, cursorIndex + 1 + pageSize);
    const response: GetFilesResponse = {
        files: page.map((document) => ({
            fileId: document.id,
            sortFieldValue: String(sortValue(document, sortByField)),
            sortId: [sortValue(document, sortByField), document.id],
        })),
        sortByField,
    };
    return json(GetFilesResponseToJSON(response));
});

const uploadHandler = http.post(/\/api\/v1\/files$/, () =>
    error("File uploads are not available in demo mode", 501),
);

const filesBulkUpdateHandler = http.put(
    /\/api\/v1\/files$/,
    async ({ request }) => {
        const parsed = await parseBody(request);
        if (!parsed.ok) return parsed.response;
        const query = objectValue(parsed.value.query);
        const requestBody = objectValue(parsed.value.request);
        const updates = requestBody ? updateValues(requestBody) : undefined;
        if (!query || typeof query.search_string !== "string" || !updates?.ok)
            return error("A valid query and update request are required", 422);
        const result = safeSearch(query.search_string);
        if (!result.ok) return result.response;
        result.documents.forEach((document) =>
            updateDocument(document.id, updates.value),
        );
        return empty(202);
    },
);

const previewHandler = http.get(
    /\/api\/v1\/files\/([^/]+)\/preview$/,
    ({ request }) => {
        const document = getDocument(
            fileIdFromRequest(request, /\/files\/([^/]+)\/preview$/),
        );
        return document
            ? json(
                  GetFilePreviewResponseToJSON(
                      documentPreview(
                          document,
                          queryFromUrl(new URL(request.url)),
                      ),
                  ),
              )
            : error("Document not found", 404);
    },
);

const binaryHandler = http.get(
    /\/api\/v1\/files\/([^/]+)\/(download|thumbnail\/[^/]+|rendered\/[^/]+)$/,
    async ({ request }) => {
        const match = new URL(request.url).pathname.match(
            /\/files\/([^/]+)\/(download|thumbnail\/[^/]+|rendered\/[^/]+)$/,
        );
        const document = getDocument(decodeURIComponent(match?.[1] ?? ""));
        if (!document) return error("Document not found", 404);
        const binaryPath = match?.[2] ?? "";
        const assetUrl =
            binaryPath === "download"
                ? document.downloadUrl
                : binaryPath.startsWith("thumbnail/")
                  ? binaryPath.slice("thumbnail/".length) ===
                    DEMO_THUMBNAIL_FILE_ID
                      ? document.thumbnail?.url
                      : undefined
                  : getRenderedAssetUrl(
                        document,
                        binaryPath.slice("rendered/".length),
                    );
        if (assetUrl) {
            const response = await fetch(assetUrl);
            if (response.ok)
                return new HttpResponse(await response.arrayBuffer(), {
                    headers: {
                        "Content-Type":
                            response.headers.get("Content-Type") ??
                            document.mimeType,
                    },
                });
        }
        if (binaryPath === "download")
            return new HttpResponse(document.data, {
                headers: { "Content-Type": document.mimeType },
            });
        return error("Preview not found", 404);
    },
);

const fileTagsAddHandler = http.post(
    /\/api\/v1\/files\/([^/]+)\/tags$/,
    async ({ request }) => {
        const parsed = await parseBody(request);
        if (!parsed.ok) return parsed.response;
        const tags = stringArrayValue(parsed.value.tags);
        if (!tags) return error("tags must be an array of strings", 422);
        const updated = addTags(
            fileIdFromRequest(request, /\/files\/([^/]+)\/tags$/),
            tags,
        );
        return updated ? empty(202) : error("Document not found", 404);
    },
);

const fileTagDeleteHandler = http.delete(
    /\/api\/v1\/files\/([^/]+)\/tags\/([^/]+)$/,
    ({ request }) => {
        const match = new URL(request.url).pathname.match(
            /\/files\/([^/]+)\/tags\/([^/]+)$/,
        );
        const updated = removeTag(
            decodeURIComponent(match?.[1] ?? ""),
            decodeURIComponent(match?.[2] ?? ""),
        );
        return updated ? empty(202) : error("Document not found", 404);
    },
);

const taskHandler = http.post(
    /\/api\/v1\/files\/([^/]+)\/(summarize|translate|index|image_description)$/,
    async ({ request }) => {
        const match = new URL(request.url).pathname.match(
            /\/files\/([^/]+)\/(summarize|translate|index|image_description)$/,
        );
        const fileId = decodeURIComponent(match?.[1] ?? "");
        const operation = match?.[2];
        let task: DemoTask;
        if (operation === "translate") {
            const parsed = await parseBody(request);
            if (!parsed.ok) return parsed.response;
            const language = stringValue(parsed.value.lang)?.trim();
            if (!language) return error("lang is required", 422);
            task = { kind: "translate", language };
        } else if (operation === "summarize") {
            task = { kind: "summarize" };
        } else if (operation === "image_description") {
            task = { kind: "image_description" };
        } else {
            task = { kind: "index" };
        }
        if (!scheduleTask(fileId, task))
            return error("Document not found", 404);
        return empty(202);
    },
);

const fileDetailHandler = http.get(
    /\/api\/v1\/files\/([^/]+)$/,
    ({ request }) => {
        const document = getDocument(
            fileIdFromRequest(request, /\/files\/([^/]+)$/),
        );
        return document
            ? json(
                  GetFileResponseToJSON(
                      documentDetail(
                          document,
                          queryFromUrl(new URL(request.url)),
                      ),
                  ),
              )
            : error("Document not found", 404);
    },
);

const fileUpdateHandler = http.put(
    /\/api\/v1\/files\/([^/]+)$/,
    async ({ request }) => {
        const parsed = await parseBody(request);
        if (!parsed.ok) return parsed.response;
        const updates = updateValues(parsed.value);
        if (!updates.ok) return error("Invalid document update", 422);
        const fileId = fileIdFromRequest(request, /\/files\/([^/]+)$/);
        if (!updateDocument(fileId, updates.value))
            return error("Document not found", 404);
        scheduleDemoTimeout(
            () =>
                sendToChannel(fileId, {
                    type: "fileUpdate",
                    fileId,
                }),
            100,
        );
        return empty(202);
    },
);

const unhandledFilesHandler = http.all(
    /\/api\/v1\/files(?:\/.*)?$/,
    ({ request }) =>
        error(
            `Method not allowed or unhandled demo route: ${request.method}`,
            405,
        ),
);

export const filesHandlers = [
    queryHandler,
    countHandler,
    tagsListHandler,
    tagsBulkAddHandler,
    globalTagDeleteHandler,
    availableTermsHandler,
    availableHistogramHandler,
    termsHandler,
    histogramHandler,
    treeSpineHandler,
    treeHandler,
    filenameHandler,
    filesListHandler,
    uploadHandler,
    filesBulkUpdateHandler,
    previewHandler,
    binaryHandler,
    fileTagsAddHandler,
    fileTagDeleteHandler,
    taskHandler,
    fileDetailHandler,
    fileUpdateHandler,
    unhandledFilesHandler,
];
