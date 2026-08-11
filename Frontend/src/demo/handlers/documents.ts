import type {
    GetFilePreviewResponse,
    GetFileResponse,
    TaskRecord,
} from "@app/api/generated";

import { parseDemoQuery } from "../query";
import {
    DEMO_BROWSER_PDF_FILE_ID,
    DEMO_IMAGE_FILE_ID,
    DEMO_OFFICE_PDF_FILE_ID,
    DEMO_THUMBNAIL_FILE_ID,
    type DemoDocument,
} from "../repository";

export interface TreeNodeWire {
    full_path: string;
    file_count: number;
    file_id?: string;
    unseen_count?: number;
    is_unseen?: boolean;
    flagged_count?: number;
    is_flagged?: boolean;
    direct_children_count?: number;
}

const pathSegments = (path: string): string[] =>
    path.split("/").filter((segment) => segment.length > 0);

// Demo document paths use /path format; the real backend uses //source/path.
// The tree emits //path to match what ClickableFilePath generates when
// deriving parent_path filter values.
const toApiPath = (internalPath: string): string =>
    internalPath === "/" ? "/" : `/${internalPath}`;

const toInternalPath = (apiPath: string | null): string => {
    if (!apiPath || apiPath === "/" || apiPath === "//") return "/";
    return apiPath.startsWith("//") ? apiPath.slice(1) : apiPath;
};

const directoryTreeNode = (
    documents: DemoDocument[],
    directoryPath: string,
): TreeNodeWire => {
    const prefix = directoryPath === "/" ? "/" : `${directoryPath}/`;
    const descendants = documents.filter((document) =>
        document.path.startsWith(prefix),
    );
    const directChildrenCount = descendants.filter(
        (document) => !document.path.slice(prefix.length).includes("/"),
    ).length;
    return {
        full_path: toApiPath(directoryPath),
        file_count: descendants.length,
        unseen_count: descendants.filter((document) => !document.seen).length,
        flagged_count: descendants.filter((document) => document.flagged)
            .length,
        direct_children_count: directChildrenCount,
    };
};

export const documentTreeNode = (
    document: DemoDocument,
    allDocuments: DemoDocument[],
): TreeNodeWire => {
    const prefix = `${document.path}/`;
    const children = allDocuments.filter((d) => d.path.startsWith(prefix));
    return {
        full_path: toApiPath(document.path),
        file_count: children.length,
        file_id: document.id,
        unseen_count: children.filter((d) => !d.seen).length,
        is_unseen: !document.seen,
        flagged_count: children.filter((d) => d.flagged).length,
        is_flagged: document.flagged,
        direct_children_count: 0,
    };
};

export const treeRootStats = (documents: DemoDocument[]): TreeNodeWire => ({
    full_path: "/",
    file_count: documents.length,
    unseen_count: documents.filter((d) => !d.seen).length,
    flagged_count: documents.filter((d) => d.flagged).length,
    direct_children_count: documents.filter(
        (d) => pathSegments(d.path).length === 1,
    ).length,
});

export const treeChildren = (
    documents: DemoDocument[],
    parentPath: string | null,
): TreeNodeWire[] => {
    const internalParent = toInternalPath(parentPath);
    const parentSegments =
        internalParent === "/" ? [] : pathSegments(internalParent);
    const childDirectories = new Set<string>();
    const childFiles = new Map<string, DemoDocument>();

    documents.forEach((document) => {
        const segments = pathSegments(document.path);
        const parentMatches = parentSegments.every(
            (segment, index) => segments[index] === segment,
        );
        if (!parentMatches || segments.length <= parentSegments.length) return;
        if (segments.length === parentSegments.length + 1) {
            childFiles.set(document.path, document);
            return;
        }
        childDirectories.add(
            `/${segments.slice(0, parentSegments.length + 1).join("/")}`,
        );
    });

    const children = new Map<string, TreeNodeWire>(
        [...childDirectories]
            .sort()
            .map((path) => [
                toApiPath(path),
                directoryTreeNode(documents, path),
            ]),
    );
    [...childFiles.values()]
        .sort((left, right) => left.path.localeCompare(right.path))
        .forEach((document) => {
            const apiPath = toApiPath(document.path);
            const fileNode = documentTreeNode(document, documents);
            children.set(apiPath, {
                ...fileNode,
                ...children.get(apiPath),
                file_id: fileNode.file_id,
                is_unseen: fileNode.is_unseen,
                is_flagged: fileNode.is_flagged,
            });
        });
    return [...children.values()].sort((left, right) =>
        left.full_path.localeCompare(right.full_path),
    );
};

export const treeSpine = (
    documents: DemoDocument[],
    fullPath: string | null,
): TreeNodeWire[] => {
    const internalPath = toInternalPath(fullPath);
    const document = documents.find((item) => item.path === internalPath);
    if (!document) return [];
    const segments = pathSegments(document.path);
    const directories = segments
        .slice(0, -1)
        .map((_, index) => `/${segments.slice(0, index + 1).join("/")}`);
    return [
        ...directories.map((path) => directoryTreeNode(documents, path)),
        documentTreeNode(document, documents),
    ];
};

export const documentPreview = (
    document: DemoDocument,
    query: string,
): GetFilePreviewResponse => ({
    fileId: document.id,
    parentId: document.parentId,
    tags: document.tags,
    flagged: document.flagged,
    hidden: document.hidden,
    seen: document.seen,
    contentIsTruncated: document.contentTruncated ?? false,
    name: document.name,
    path: document.path,
    thumbnailFileId: document.thumbnail ? DEMO_THUMBNAIL_FILE_ID : undefined,
    thumbnailTotalFrames: document.thumbnail?.totalFrames,
    attachments: document.attachments,
    attachmentsTotalCount: document.attachments?.length ?? 0,
    fileExtension: document.extension,
    highlight: parseDemoQuery(query).highlights(document),
    detectedLanguage: document.language,
    attachmentsSkipped: document.attachmentsSkipped ?? false,
    isSpam: document.isSpam ?? false,
    state: document.state,
    mimeType: document.mimeType,
    mimeTypeGroup: document.mimeType.split(
        "/",
    )[0] as GetFilePreviewResponse["mimeTypeGroup"],
    fields: {
        content: {
            value: document.content.slice(0, 220),
            isTruncated: document.content.length > 220,
        },
        short_name: { value: document.name },
        extension: { value: document.extension },
        ...(document.summary ? { summary: { value: document.summary } } : {}),
        ...(document.imageDescription
            ? {
                  image_description: {
                      value: document.imageDescription,
                  },
              }
            : {}),
        ...(document.translations.length > 0
            ? {
                  translation_preview: {
                      value: document.translations[
                          document.translations.length - 1
                      ].text.slice(0, 1000),
                      isTruncated:
                          document.translations[
                              document.translations.length - 1
                          ].text.length > 1000,
                  },
              }
            : {}),
        ...(document.dcTitle ? { dc_title: { value: document.dcTitle } } : {}),
        ...(document.dcDescription
            ? { dc_description: { value: document.dcDescription } }
            : {}),
        ...(document.dcSubject
            ? {
                  dc_subject: {
                      value: Array.isArray(document.dcSubject)
                          ? document.dcSubject.join(", ")
                          : document.dcSubject,
                  },
              }
            : {}),
        ...(document.authors.length > 0
            ? { dc_creator: { value: document.authors.join(", ") } }
            : {}),
        ...(document.messageFrom
            ? {
                  message_from: {
                      value: Array.isArray(document.messageFrom)
                          ? document.messageFrom.join(", ")
                          : document.messageFrom,
                  },
              }
            : {}),
        ...(document.messageTo
            ? {
                  message_to: {
                      value: Array.isArray(document.messageTo)
                          ? document.messageTo.join(", ")
                          : document.messageTo,
                  },
              }
            : {}),
        ...(document.messageCc
            ? {
                  message_cc: {
                      value: Array.isArray(document.messageCc)
                          ? document.messageCc.join(", ")
                          : document.messageCc,
                  },
              }
            : {}),
    },
});

const documentRaw = (document: DemoDocument): string =>
    JSON.stringify({
        id_: document.id,
        state: document.state,
        parent_id: document.parentId,
        full_name: document.path,
        full_path: document.path,
        short_name: document.name,
        extension: `.${document.extension}`,
        uploaded_datetime: document.uploadedAt,
        tika_meta: {
            dcterms_created: document.createdAt,
            dcterms_modified: document.modifiedAt,
            dc_creator: document.authors,
        },
        size: document.size,
        tags: document.tags,
        summary: document.summary,
        image_description: document.imageDescription,
        flagged: document.flagged,
        seen: document.seen,
        detected_language: document.language,
        magic_file_type: document.mimeType,
        trufflehog_secrets: document.secrets,
        source: document.source,
    });

const demoTasks = (document: DemoDocument): TaskRecord[] => {
    const base = new Date(document.uploadedAt).getTime();
    const run = (
        offsetSeconds: number,
        durationMs: number,
        taskId: string,
    ) => ({
        startedAt: new Date(base + offsetSeconds * 1000),
        finishedAt: new Date(base + offsetSeconds * 1000 + durationMs),
        duration: durationMs,
        taskId: taskId,
    });
    if (document.state === "failed") {
        const args = JSON.stringify(
            {
                file_id: document.id,
                full_name: document.path,
                mime_type: document.mimeType,
                size: document.size,
            },
            null,
            2,
        );
        return [
            {
                taskName: "worker.index_file.index_file_task.index_file_task",
                retried: [
                    {
                        ...run(5, 1800, "99000000-0000-4000-8000-000000000001"),
                        arguments: args,
                        exception:
                            "Traceback (most recent call last):\n" +
                            '  File "/app/worker/index_file/tasks/index_file.py", line 42, in index_file_task\n' +
                            "    extracted = extraction_service.extract(file)\n" +
                            '  File "/app/worker/index_file/domain/extraction_service.py", line 87, in extract\n' +
                            "    response = self._tika_client.parse(file.stream, mime_type=file.mime_type)\n" +
                            '  File "/app/worker/index_file/infra/tika_client.py", line 31, in parse\n' +
                            '    raise ExtractionError(f"Tika returned status {resp.status_code}")\n' +
                            "worker.index_file.domain.errors.ExtractionError: Tika returned status 422",
                    },
                    {
                        ...run(
                            75,
                            2100,
                            "99000000-0000-4000-8000-000000000002",
                        ),
                        arguments: args,
                        exception:
                            "Traceback (most recent call last):\n" +
                            '  File "/app/worker/index_file/tasks/index_file.py", line 42, in index_file_task\n' +
                            "    extracted = extraction_service.extract(file)\n" +
                            '  File "/app/worker/index_file/domain/extraction_service.py", line 87, in extract\n' +
                            "    response = self._tika_client.parse(file.stream, mime_type=file.mime_type)\n" +
                            '  File "/app/worker/index_file/infra/tika_client.py", line 31, in parse\n' +
                            '    raise ExtractionError(f"Tika returned status {resp.status_code}")\n' +
                            "worker.index_file.domain.errors.ExtractionError: Tika returned status 422",
                    },
                ],
                failed: [
                    {
                        ...run(
                            155,
                            950,
                            "99000000-0000-4000-8000-000000000003",
                        ),
                        arguments: args,
                        exception:
                            "Traceback (most recent call last):\n" +
                            '  File "/app/worker/index_file/tasks/index_file.py", line 42, in index_file_task\n' +
                            "    extracted = extraction_service.extract(file)\n" +
                            '  File "/app/worker/index_file/domain/extraction_service.py", line 87, in extract\n' +
                            "    response = self._tika_client.parse(file.stream, mime_type=file.mime_type)\n" +
                            '  File "/app/worker/index_file/infra/tika_client.py", line 31, in parse\n' +
                            '    raise ExtractionError(f"Tika returned status {resp.status_code}")\n' +
                            "worker.index_file.domain.errors.ExtractionError: Tika returned status 422",
                    },
                ],
            },
        ];
    }
    const tasks: TaskRecord[] = [
        {
            taskName: "worker.index_file.index_file_task.index_file_task",
            succeeded: [run(5, 3200, "10000000-0000-4000-8000-000000000001")],
        },
    ];
    if (document.summary) {
        tasks.push({
            taskName:
                "worker.index_file.summarize_file_task.summarize_file_task",
            succeeded: [run(12, 8400, "10000000-0000-4000-8000-000000000002")],
        });
    }
    if (document.imageDescription) {
        tasks.push({
            taskName:
                "worker.index_file.image_description_task.image_description_task",
            succeeded: [run(9, 5100, "10000000-0000-4000-8000-000000000003")],
        });
    }
    return tasks;
};

export const documentDetail = (
    document: DemoDocument,
    query: string,
): GetFileResponse => ({
    fileId: document.id,
    highlight: documentPreview(document, query).highlight,
    content: document.content,
    name: document.name,
    fullPath: document.path,
    languageTranslations: document.translations,
    detectedLanguage: document.language,
    raw: documentRaw(document),
    summary: document.summary,
    imageDescription: document.imageDescription,
    type: document.mimeType,
    renderedFile: {
        imageFileId: document.rendered?.imageUrl
            ? DEMO_IMAGE_FILE_ID
            : undefined,
        officePdfFileId: document.rendered?.officePdfUrl
            ? DEMO_OFFICE_PDF_FILE_ID
            : undefined,
        browserPdfFileId: document.rendered?.browserPdfUrl
            ? DEMO_BROWSER_PDF_FILE_ID
            : undefined,
    },
    tasks: demoTasks(document),
});
