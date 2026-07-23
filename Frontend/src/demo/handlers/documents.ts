import type {
    GetFilePreviewResponse,
    GetFileResponse,
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
}

const pathSegments = (path: string): string[] =>
    path.split("/").filter((segment) => segment.length > 0);

const directoryTreeNode = (
    documents: DemoDocument[],
    directoryPath: string,
): TreeNodeWire => {
    const prefix = directoryPath === "/" ? "/" : `${directoryPath}/`;
    const descendants = documents.filter((document) =>
        document.path.startsWith(prefix),
    );
    return {
        full_path: directoryPath,
        file_count: descendants.length,
        unseen_count: descendants.filter((document) => !document.seen).length,
        flagged_count: descendants.filter((document) => document.flagged)
            .length,
    };
};

const documentTreeNode = (document: DemoDocument): TreeNodeWire => ({
    full_path: document.path,
    file_count: 1,
    file_id: document.id,
    unseen_count: 0,
    is_unseen: !document.seen,
    flagged_count: 0,
    is_flagged: document.flagged,
});

export const treeChildren = (
    documents: DemoDocument[],
    parentPath: string | null,
): TreeNodeWire[] => {
    const normalizedParent = parentPath || "/";
    const parentSegments =
        normalizedParent === "/" ? [] : pathSegments(normalizedParent);
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

    return [
        ...[...childDirectories]
            .sort()
            .map((path) => directoryTreeNode(documents, path)),
        ...[...childFiles.values()]
            .sort((left, right) => left.path.localeCompare(right.path))
            .map(documentTreeNode),
    ];
};

export const treeSpine = (
    documents: DemoDocument[],
    fullPath: string | null,
): TreeNodeWire[] => {
    const document = documents.find((item) => item.path === fullPath);
    if (!document) return [];
    const segments = pathSegments(document.path);
    const directories = segments
        .slice(0, -1)
        .map((_, index) => `/${segments.slice(0, index + 1).join("/")}`);
    return [
        ...directories.map((path) => directoryTreeNode(documents, path)),
        documentTreeNode(document),
    ];
};

const DEMO_TASK_IDS = [
    "10000000-0000-4000-8000-000000000001",
    "10000000-0000-4000-8000-000000000002",
    "10000000-0000-4000-8000-000000000003",
];

export const documentPreview = (
    document: DemoDocument,
    query: string,
): GetFilePreviewResponse => ({
    fileId: document.id,
    tags: document.tags,
    flagged: document.flagged,
    hidden: document.hidden,
    seen: document.seen,
    content: document.content,
    contentPreviewIsTruncated: document.content.length > 220,
    contentIsTruncated: false,
    name: document.name,
    path: document.path,
    thumbnailFileId: document.thumbnail ? DEMO_THUMBNAIL_FILE_ID : undefined,
    thumbnailTotalFrames: document.thumbnail?.totalFrames,
    attachments: document.attachments,
    attachmentsTotalCount: document.attachments?.length ?? 0,
    fileExtension: document.extension,
    highlight: parseDemoQuery(query).highlights(document),
    tasksSucceeded:
        document.state === "processed" ? DEMO_TASK_IDS : [DEMO_TASK_IDS[0]],
    tasksRetried: [],
    tasksFailed: [],
    summary: document.summary,
    imageDescription: document.imageDescription,
    detectedLanguage: document.language,
    attachmentsSkipped: false,
    isSpam: false,
});

const documentRaw = (document: DemoDocument): string =>
    JSON.stringify({
        id_: document.id,
        state: document.state,
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

export const documentDetail = (
    document: DemoDocument,
    query: string,
): GetFileResponse => ({
    fileId: document.id,
    highlight: documentPreview(document, query).highlight,
    content: document.content,
    name: document.name,
    fullPath: document.path,
    languageTranslations: [],
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
});
