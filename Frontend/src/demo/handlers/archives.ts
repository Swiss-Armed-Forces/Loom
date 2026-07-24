import { http, HttpResponse } from "msw";

import { type ArchivesModel, ArchivesModelToJSON } from "@app/api/generated";

import { DemoQueryError } from "../query";
import {
    addArchive,
    getArchive,
    getArchives,
    hideArchive,
} from "../repository";

import { empty, error, json, objectValue, parseBody } from "./shared";

const archiveId = (request: Request): string => {
    const match = new URL(request.url).pathname.match(/\/archive\/([^/]+)$/);
    return decodeURIComponent(match?.[1] ?? "");
};

const listHandler = http.get(/\/api\/v1\/archive$/, () => {
    const items = getArchives();
    const response: ArchivesModel = {
        clean: true,
        hits: items.map((archive) => ({
            meta: {
                shortName: archive.name,
                query: { searchString: archive.query },
                updatedDatetime: archive.updatedAt,
            },
            content: {
                state: "processed",
                size: archive.size,
                tasksSucceeded: [],
                tasksRetried: [],
                tasksFailed: [],
            },
            sha256: archive.sha256,
            hidden: archive.hidden,
            fileId: archive.id,
        })),
        total: items.length,
        found: items.length,
        hasMore: false,
        currentPage: 0,
    };
    return json(ArchivesModelToJSON(response));
});

const createHandler = http.post(/\/api\/v1\/archive$/, async ({ request }) => {
    const parsed = await parseBody(request);
    if (!parsed.ok) return parsed.response;
    const query = objectValue(parsed.value.query);
    if (!query || typeof query.search_string !== "string")
        return error("query.search_string is required", 422);
    try {
        const archive = addArchive(query.search_string);
        return json({ archive_id: archive.id }, 201);
    } catch (reason) {
        return error(
            reason instanceof DemoQueryError
                ? reason.message
                : "Invalid archive query",
            400,
        );
    }
});

const importHandler = http.post(/\/api\/v1\/archive\/import$/, () =>
    error("Archive imports are not available in demo mode", 501),
);

const encryptionKeyHandler = http.get(
    /\/api\/v1\/archive\/encryption-key$/,
    () => json({ encryption_key: null }),
);

const hideHandler = http.put(/\/api\/v1\/archive\/([^/]+)$/, ({ request }) =>
    hideArchive(archiveId(request))
        ? empty(202)
        : error("Archive not found", 404),
);

const downloadHandler = http.get(
    /\/api\/v1\/archive\/([^/]+)$/,
    ({ request }) => {
        const archive = getArchive(archiveId(request));
        return archive
            ? new HttpResponse(`Offline Loom demo archive: ${archive.name}`, {
                  headers: { "Content-Type": "application/zip" },
              })
            : error("Archive not found", 404);
    },
);

const unhandledArchiveHandler = http.all(
    /\/api\/v1\/archive(?:\/.*)?$/,
    ({ request }) =>
        error(
            `Method not allowed or unhandled demo route: ${request.method}`,
            405,
        ),
);

export const archiveHandlers = [
    listHandler,
    createHandler,
    importHandler,
    encryptionKeyHandler,
    hideHandler,
    downloadHandler,
    unhandledArchiveHandler,
];
