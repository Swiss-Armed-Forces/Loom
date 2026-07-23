import { setupServer } from "msw/node";
import {
    afterAll,
    afterEach,
    beforeAll,
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from "vitest";

import { ArchivesApi, Configuration, FilesApi } from "@app/api/generated";

import { handlers, resetDemoHandlerState } from "./handlers";
import { clearDemoTimers, resetDemoRepository } from "./repository";

interface TreeNodeResponse {
    nodes: Array<{ full_path: string; file_count: number; file_id?: string }>;
    next_page_cursor?: string;
}

const responseJson = async <Response>(response: globalThis.Response) =>
    (await response.json()) as Response;

const server = setupServer(...handlers);

describe("demo API handlers", () => {
    beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
    beforeEach(() => {
        resetDemoRepository();
        resetDemoHandlerState();
    });
    afterEach(() => server.resetHandlers());
    afterAll(() => {
        clearDemoTimers();
        server.close();
    });

    it("serves search results and matching counts", async () => {
        const results = await fetch(
            "http://loom.test/api/v1/files?search_string=tags%3Asecurity",
        ).then((response) => response.json());
        const count = await fetch(
            "http://loom.test/api/v1/files/count?search_string=tags%3Asecurity",
        ).then((response) => response.json());

        expect(results.files).toHaveLength(1);
        expect(results.files[0].file_id).toBe(
            "11111111-1111-4111-8111-111111111111",
        );
        expect(count).toEqual({ total_files: 1 });
    });

    it("serves generated-client requests below a Pages subpath", async () => {
        const filesApi = new FilesApi(
            new Configuration({
                basePath: "http://loom.test/loom/api",
            }),
        );

        const results = await filesApi.getFilesV1FilesGet({
            searchString: "tags:security",
        });

        expect(results.files).toHaveLength(1);
        expect(results.files[0].fileId).toBe(
            "11111111-1111-4111-8111-111111111111",
        );
    });

    it("paginates generated-client requests without repeating documents", async () => {
        const filesApi = new FilesApi(
            new Configuration({ basePath: "http://loom.test/api" }),
        );
        const first = await filesApi.getFilesV1FilesGet({
            searchString: "*",
            pageSize: 2,
        });
        const second = await filesApi.getFilesV1FilesGet({
            searchString: "*",
            pageSize: 2,
            sortId: first.files.at(-1)?.sortId,
        });

        expect(first.files).toHaveLength(2);
        expect(second.files).toHaveLength(2);
        expect(second.files.map((file) => file.fileId)).not.toEqual(
            first.files.map((file) => file.fileId),
        );
        expect(
            second.files.some((file) =>
                first.files.some(
                    (firstFile) => firstFile.fileId === file.fileId,
                ),
            ),
        ).toBe(false);
    });

    it("returns backend-compatible JSON in raw file details", async () => {
        const filesApi = new FilesApi(
            new Configuration({ basePath: "http://loom.test/api" }),
        );
        const fileId = "11111111-1111-4111-8111-111111111111";

        const detail = await filesApi.getFileV1FilesFileIdGet({ fileId });

        expect(JSON.parse(detail.raw)).toMatchObject({
            id_: fileId,
            short_name: "John Smith - Network Security.txt",
            source: "api-upload",
            tika_meta: {
                dc_creator: ["Jon Smith"],
            },
        });
    });

    it("returns generated-client-compatible previews and statistics", async () => {
        const preview = await fetch(
            "http://loom.test/api/v1/files/22222222-2222-4222-8222-222222222222/preview?search_string=invoice",
        ).then((response) => response.json());
        const stats = await fetch(
            "http://loom.test/api/v1/files/stats/terms/extension?search_string=*",
        ).then((response) => response.json());

        expect(preview).toMatchObject({
            file_extension: "eml",
            tags: ["email", "interesting"],
            thumbnail_file_id: "thumbnail.png",
            thumbnail_total_frames: 1,
        });
        expect(stats.file_count).toBe(9);
        expect(stats.data).toContainEqual({ name: "txt", hits_count: 3 });
    });

    it("returns only query-relevant highlight fields", async () => {
        const fileId = "11111111-1111-4111-8111-111111111111";
        const preview = await fetch(
            `http://loom.test/api/v1/files/${fileId}/preview?search_string=tags%3Asecurity`,
        ).then((response) => response.json());
        const detail = await fetch(
            `http://loom.test/api/v1/files/${fileId}?search_string=tags%3Asecurity`,
        ).then((response) => response.json());
        const matchAll = await fetch(
            `http://loom.test/api/v1/files/${fileId}/preview?search_string=*`,
        ).then((response) => response.json());

        expect(preview.highlight).toEqual({
            tags: ["<highlight>security</highlight>"],
        });
        expect(detail.highlight).toEqual(preview.highlight);
        expect(matchAll.highlight).toEqual({});
    });

    it("reports real renderer types and no fabricated archive preview", async () => {
        const emailDetail = await fetch(
            "http://loom.test/api/v1/files/22222222-2222-4222-8222-222222222222?search_string=*",
        ).then((response) => response.json());
        const archiveDetail = await fetch(
            "http://loom.test/api/v1/files/55555555-5555-4555-8555-555555555555?search_string=*",
        ).then((response) => response.json());
        const archivePreview = await fetch(
            "http://loom.test/api/v1/files/55555555-5555-4555-8555-555555555555/preview?search_string=*",
        ).then((response) => response.json());

        expect(emailDetail.rendered_file).toEqual({
            image_file_id: "rendered-image.png",
            office_pdf_file_id: "rendered-office.pdf",
        });
        expect(archiveDetail.rendered_file).toEqual({});
        expect(archivePreview.thumbnail_file_id).toBeUndefined();
        expect(archivePreview.thumbnail_total_frames).toBeUndefined();
    });

    it("returns statistics for the requested histogram and grouping fields", async () => {
        const available = await fetch(
            "http://loom.test/api/v1/files/stats/histogram",
        ).then((response) => responseJson<Array<{ id: string }>>(response));
        const stats = await fetch(
            "http://loom.test/api/v1/files/stats/histogram/size/grouped/tags?search_string=*",
        ).then((response) =>
            responseJson<{
                stat: string;
                group_by: string;
                histogram_type: string;
                key: string;
                min_value: number;
                max_value: number;
                data: Array<{ groups: Record<string, number> }>;
            }>(response),
        );

        expect(available.map((item) => item.id)).toContain(
            "tika_meta.dcterms_created",
        );
        expect(stats).toMatchObject({
            stat: "size",
            group_by: "tags",
            histogram_type: "number",
            key: "size",
            min_value: 233,
            max_value: 2_572_288,
        });
        expect(
            stats.data.some((bucket) => bucket.groups.interesting === 1),
        ).toBe(true);
    });

    it("returns direct folder tree children without duplicating leaf nodes", async () => {
        const root = await fetch(
            "http://loom.test/api/v1/files/tree?search_string=*",
        ).then((response) => responseJson<TreeNodeResponse>(response));
        const mail = await fetch(
            "http://loom.test/api/v1/files/tree?search_string=*&node_path=%2FMail",
        ).then((response) => responseJson<TreeNodeResponse>(response));
        const inbox = await fetch(
            "http://loom.test/api/v1/files/tree?search_string=*&node_path=%2FMail%2FInbox",
        ).then((response) => responseJson<TreeNodeResponse>(response));
        const emailLeaf = await fetch(
            "http://loom.test/api/v1/files/tree?search_string=*&node_path=%2FMail%2FInbox%2Fbasic_email.eml",
        ).then((response) => responseJson<TreeNodeResponse>(response));

        expect(root.nodes.map((node) => node.full_path)).toContain("/Crawler");
        expect(mail.nodes).toEqual([
            expect.objectContaining({
                full_path: "/Mail/Inbox",
                file_count: 1,
            }),
        ]);
        expect(inbox.nodes).toEqual([
            expect.objectContaining({
                full_path: "/Mail/Inbox/basic_email.eml",
                file_id: "22222222-2222-4222-8222-222222222222",
            }),
        ]);
        expect(emailLeaf.nodes).toEqual([]);
    });

    it("paginates folder nodes with a stable path cursor", async () => {
        const first = await fetch(
            "http://loom.test/api/v1/files/tree?search_string=*",
        ).then((response) => responseJson<TreeNodeResponse>(response));
        const second = await fetch(
            `http://loom.test/api/v1/files/tree?search_string=*&after=${encodeURIComponent(first.next_page_cursor ?? "")}`,
        ).then((response) => responseJson<TreeNodeResponse>(response));

        expect(first.nodes).toHaveLength(3);
        expect(first.next_page_cursor).toBeDefined();
        expect(second.nodes).toHaveLength(3);
        expect(
            second.nodes.some((node) =>
                first.nodes.some(
                    (firstNode) => firstNode.full_path === node.full_path,
                ),
            ),
        ).toBe(false);
    });

    it("returns a single root-to-file folder tree spine", async () => {
        const spine = await fetch(
            "http://loom.test/api/v1/files/tree/spine?search_string=*&full_path=%2FMail%2FInbox%2Fbasic_email.eml",
        ).then((response) => responseJson<TreeNodeResponse>(response));

        expect(spine.nodes.map((node) => node.full_path)).toEqual([
            "/Mail",
            "/Mail/Inbox",
            "/Mail/Inbox/basic_email.eml",
        ]);
    });

    it("persists tag mutations for subsequent API reads", async () => {
        const id = "11111111-1111-4111-8111-111111111111";
        const update = await fetch(`http://loom.test/api/v1/files/${id}/tags`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tags: ["reviewed"] }),
        });
        const preview = await fetch(
            `http://loom.test/api/v1/files/${id}/preview?search_string=*`,
        ).then((response) => response.json());

        expect(preview.tags).toContain("reviewed");
        expect(update.status).toBe(202);
    });

    it("serves downloadable archives whose membership can be searched", async () => {
        const configuration = new Configuration({
            basePath: "http://loom.test/api",
        });
        const archivesApi = new ArchivesApi(configuration);
        const filesApi = new FilesApi(configuration);

        const archives = await archivesApi.getAllArchivesV1ArchiveGet();
        const archive = archives.hits[0];
        const files = await filesApi.getFilesV1FilesGet({
            searchString: `archives:${archive.fileId}`,
        });

        expect(archive.sha256).toMatch(/^[a-f0-9]{64}$/);
        expect(archive.sha256Encrypted).toBeUndefined();
        expect(files.files).toHaveLength(3);
    });

    it("creates archives with the backend status and searchable membership", async () => {
        const created = await fetch("http://loom.test/api/v1/archive", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query: { search_string: "tags:security" },
            }),
        });
        const body = await responseJson<{ archive_id: string }>(created);
        const files = await fetch(
            `http://loom.test/api/v1/files/count?search_string=${encodeURIComponent(`archives:${body.archive_id}`)}`,
        ).then((response) => response.json());

        expect(created.status).toBe(201);
        expect(files.total_files).toBe(1);
    });

    it("applies bulk tasks to every document matching the request query", async () => {
        vi.useFakeTimers();
        resetDemoRepository();
        try {
            const scheduled = await fetch(
                "http://loom.test/api/v1/files/translation",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        lang: "de",
                        query: { search_string: "tags:interesting" },
                    }),
                },
            );

            expect(scheduled.status).toBe(202);
            await vi.advanceTimersByTimeAsync(2_100);

            const translated = await fetch(
                "http://loom.test/api/v1/files/count?search_string=detected_language%3Ade%20AND%20tags%3Ainteresting",
            ).then((response) =>
                responseJson<{ total_files: number }>(response),
            );
            expect(translated.total_files).toBe(3);
        } finally {
            clearDemoTimers();
            vi.useRealTimers();
        }
    });

    it("keeps an AI context available for follow-up questions", async () => {
        vi.useFakeTimers();
        resetDemoRepository();
        try {
            const context = await fetch("http://loom.test/api/v1/ai", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ search_string: "tags:security" }),
            }).then((response) =>
                responseJson<{ context_id: string }>(response),
            );
            const ask = (question: string) =>
                fetch(
                    `http://loom.test/api/v1/ai/${context.context_id}/process_question`,
                    {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ question }),
                    },
                );

            expect((await ask("What is the term?")).status).toBe(202);
            await vi.runAllTimersAsync();
            expect((await ask("What is the availability?")).status).toBe(202);
        } finally {
            clearDemoTimers();
            vi.useRealTimers();
        }
    });

    it("rejects ingestion actions without mutating demo data", async () => {
        const form = new FormData();
        form.set("file", new File(["test"], "test.txt"));

        const upload = await fetch("http://loom.test/api/v1/files", {
            method: "POST",
            body: form,
        });
        const archiveImport = await fetch(
            "http://loom.test/api/v1/archive/import",
            { method: "POST", body: form },
        );
        const files = await fetch(
            "http://loom.test/api/v1/files/count?search_string=*",
        ).then((response) => response.json());
        const archives = await fetch("http://loom.test/api/v1/archive").then(
            (response) => response.json(),
        );

        expect(upload.status).toBe(501);
        expect(archiveImport.status).toBe(501);
        expect(files.total_files).toBe(9);
        expect(archives.total).toBe(1);
    });

    it("returns backend-like errors for invalid requests", async () => {
        const missingUpdate = await fetch(
            "http://loom.test/api/v1/files/missing-id",
            {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ seen: true }),
            },
        );
        const invalidBody = await fetch(
            "http://loom.test/api/v1/files/11111111-1111-4111-8111-111111111111/tags",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: "not-json",
            },
        );
        const wrongMethod = await fetch(
            "http://loom.test/api/v1/files/11111111-1111-4111-8111-111111111111/summarize",
        );
        const invalidQuery = await fetch(
            "http://loom.test/api/v1/files/count?search_string=tags%3A",
        );

        expect(missingUpdate.status).toBe(404);
        expect(invalidBody.status).toBe(422);
        expect(wrongMethod.status).toBe(405);
        expect(invalidQuery.status).toBe(400);
    });

    it("returns consistent diagnostics without contacting a backend", async () => {
        const first = await fetch("http://loom.test/api/v1/queues/stats").then(
            (response) => response.json(),
        );
        const second = await fetch("http://loom.test/api/v1/queues/stats").then(
            (response) => response.json(),
        );

        expect(first.messages_in_queues).toBeGreaterThanOrEqual(0);
        expect(second.messages_in_queues).toBe(first.messages_in_queues);
        expect(first.paused_queues).toEqual([]);
    });

    it("handles WebSocket keepalives and subscription confirmations", async () => {
        const socket = new WebSocket("ws://loom.test/api/v1/websocket");
        await new Promise<void>((resolve) =>
            socket.addEventListener("open", () => resolve(), { once: true }),
        );

        const messages: Array<Record<string, Record<string, unknown>>> = [];
        const collectMessage = (event: MessageEvent) =>
            messages.push(JSON.parse(String(event.data)));
        socket.addEventListener("message", collectMessage);

        socket.send(JSON.stringify({ message: { type: "noop" } }));
        await new Promise((resolve) => setTimeout(resolve, 25));
        expect(messages).toEqual([]);

        socket.send(
            JSON.stringify({
                message: { type: "subscribe", channels: ["demo-channel"] },
            }),
        );
        await vi.waitFor(() => expect(messages).toHaveLength(1));

        expect(socket.readyState).toBe(WebSocket.OPEN);
        expect(messages[0].message).toEqual({
            type: "subscribeConfirmation",
            channels: ["demo-channel"],
        });

        socket.send(
            JSON.stringify({
                message: { type: "unsubscribe", channels: ["demo-channel"] },
            }),
        );
        await vi.waitFor(() => expect(messages).toHaveLength(2));
        expect(messages[1].message).toEqual({
            type: "unsubscribeConfirmation",
            channels: ["demo-channel"],
        });
        socket.removeEventListener("message", collectMessage);
        socket.close();
    });

    it("publishes backend-compatible file update messages", async () => {
        const fileId = "11111111-1111-4111-8111-111111111111";
        const socket = new WebSocket("ws://loom.test/api/v1/websocket");
        await new Promise<void>((resolve) =>
            socket.addEventListener("open", () => resolve(), { once: true }),
        );
        socket.send(
            JSON.stringify({
                message: { type: "subscribe", channels: [fileId] },
            }),
        );
        await new Promise<void>((resolve) =>
            socket.addEventListener("message", () => resolve(), { once: true }),
        );

        const updateMessage = new Promise<Record<string, unknown>>((resolve) =>
            socket.addEventListener(
                "message",
                (event) =>
                    resolve(
                        JSON.parse(String(event.data)).message as Record<
                            string,
                            unknown
                        >,
                    ),
                { once: true },
            ),
        );
        const update = await fetch(`http://loom.test/api/v1/files/${fileId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ seen: true }),
        });

        await expect(updateMessage).resolves.toEqual({
            type: "fileUpdate",
            fileId,
        });
        expect(update.status).toBe(202);
        socket.close();
    });
});
