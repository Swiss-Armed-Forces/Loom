import { createDemoDocuments, INITIAL_ARCHIVE_ID } from "./fixtures";
import { parseDemoQuery } from "./query";

export interface DemoDocument {
    id: string;
    name: string;
    path: string;
    extension: string;
    mimeType: string;
    size: number;
    uploadedAt: string;
    createdAt: string;
    modifiedAt: string;
    state: "processed" | "processing" | "failed";
    tags: string[];
    content: string;
    summary: string;
    flagged: boolean;
    hidden: boolean;
    seen: boolean;
    language: string;
    authors: string[];
    secrets: string[];
    source: string;
    imageDescription?: string;
    attachments?: { id: string; name: string }[];
    archiveIds: string[];
    data: string;
    downloadUrl?: string;
    thumbnail?: {
        url: string;
        totalFrames: number;
    };
    rendered?: {
        imageUrl?: string;
        officePdfUrl?: string;
        browserPdfUrl?: string;
    };
}

export const DEMO_THUMBNAIL_FILE_ID = "thumbnail.png";
export const DEMO_IMAGE_FILE_ID = "rendered-image.png";
export const DEMO_OFFICE_PDF_FILE_ID = "rendered-office.pdf";
export const DEMO_BROWSER_PDF_FILE_ID = "rendered-browser.pdf";

export const getRenderedAssetUrl = (
    document: DemoDocument,
    renderedId: string,
): string | undefined => {
    if (renderedId === DEMO_IMAGE_FILE_ID) return document.rendered?.imageUrl;
    if (renderedId === DEMO_OFFICE_PDF_FILE_ID)
        return document.rendered?.officePdfUrl;
    if (renderedId === DEMO_BROWSER_PDF_FILE_ID)
        return document.rendered?.browserPdfUrl;
    return undefined;
};

export interface DemoArchive {
    id: string;
    name: string;
    query: string;
    size: number;
    updatedAt: string;
    hidden: boolean;
    sha256: string;
}

export type DemoTask =
    | { kind: "summarize" }
    | { kind: "translate"; language: string }
    | { kind: "image_description" }
    | { kind: "index" };

const DEMO_ARCHIVE_SHA256 = "0".repeat(64);

const createInitialArchives = (): DemoArchive[] => [
    {
        id: INITIAL_ARCHIVE_ID,
        name: "Interesting integration fixtures",
        query: "tags:interesting",
        size: 12_448,
        updatedAt: new Date().toISOString(),
        hidden: false,
        sha256: DEMO_ARCHIVE_SHA256,
    },
];

let documents = createDemoDocuments();
let archives = createInitialArchives();
let queueDepth = 0;
const pendingTimers = new Set<number>();
let publishDocumentUpdate: (fileId: string) => void = () => {};

export const setDemoDocumentUpdatePublisher = (
    publisher: (fileId: string) => void,
): void => {
    publishDocumentUpdate = publisher;
};

export const scheduleDemoTimeout = (
    callback: () => void,
    delay: number,
): void => {
    const timer = window.setTimeout(() => {
        pendingTimers.delete(timer);
        callback();
    }, delay);
    pendingTimers.add(timer);
};

export const searchDocuments = (query = "*"): DemoDocument[] => {
    const parsed = parseDemoQuery(query);
    return documents.filter(
        (document) =>
            (!document.hidden || parsed.references("hidden")) &&
            parsed.matches(document),
    );
};

export const getDocument = (id: string): DemoDocument | undefined =>
    documents.find((document) => document.id === id);

export const getDocuments = (): DemoDocument[] => documents;

export const updateDocument = (
    id: string,
    updates: Partial<Pick<DemoDocument, "flagged" | "hidden" | "seen">>,
): boolean => {
    const document = getDocument(id);
    if (!document) return false;
    Object.assign(document, updates);
    return true;
};

export const addTags = (id: string, tags: string[]): boolean => {
    const document = getDocument(id);
    if (!document) return false;
    document.tags = [...new Set([...document.tags, ...tags])].sort();
    return true;
};

export const removeTag = (id: string, tag: string): boolean => {
    const document = getDocument(id);
    if (!document) return false;
    document.tags = document.tags.filter((item) => item !== tag);
    return true;
};

export const removeTagGlobally = (tag: string): void => {
    documents.forEach((document) => removeTag(document.id, tag));
};

export const getTags = (): string[] =>
    [...new Set(documents.flatMap((document) => document.tags))].sort();

export const getArchives = (): DemoArchive[] =>
    archives.filter((item) => !item.hidden);

export const getArchive = (id: string): DemoArchive | undefined =>
    archives.find((item) => item.id === id);

export const addArchive = (query: string): DemoArchive => {
    const matchingDocuments = searchDocuments(query);
    const archive: DemoArchive = {
        id: crypto.randomUUID(),
        name: `Search archive ${archives.length + 1}`,
        query,
        size: matchingDocuments.reduce((total, item) => total + item.size, 0),
        updatedAt: new Date().toISOString(),
        hidden: false,
        sha256: DEMO_ARCHIVE_SHA256,
    };
    matchingDocuments.forEach((document) =>
        document.archiveIds.push(archive.id),
    );
    archives.unshift(archive);
    return archive;
};

export const hideArchive = (id: string): boolean => {
    const archive = archives.find((item) => item.id === id);
    if (!archive) return false;
    archive.hidden = true;
    return true;
};

const enqueueDemoTask = (onComplete: () => void): void => {
    queueDepth += 1;
    scheduleDemoTimeout(() => {
        try {
            onComplete();
        } finally {
            queueDepth = Math.max(0, queueDepth - 1);
        }
    }, 2_000);
};

export const scheduleTask = (id: string, task: DemoTask): boolean => {
    const document = getDocument(id);
    if (!document) return false;
    enqueueDemoTask(() => {
        if (task.kind === "summarize")
            document.summary = `Demo-generated summary: ${document.summary}`;
        if (task.kind === "translate") {
            document.language = task.language;
            document.content = `${document.content} (Translated for the offline demo.)`;
        }
        if (task.kind === "image_description")
            document.imageDescription ??=
                "A locally generated description of the sample image.";
        if (task.kind === "index") document.state = "processed";
        publishDocumentUpdate(document.id);
    });
    return true;
};

export const getMetrics = (): {
    messagesInQueues: number;
    estimateTimestamp?: number;
    filesPending: number;
} => {
    const pending = queueDepth;
    return {
        messagesInQueues: pending,
        estimateTimestamp:
            pending > 0 ? Date.now() / 1_000 + pending * 42 : undefined,
        filesPending: pending,
    };
};

export const resetDemoRepository = (): void => {
    clearDemoTimers();
    documents = createDemoDocuments();
    archives = createInitialArchives();
    queueDepth = 0;
    documents
        .filter((document) => document.state === "processing")
        .forEach((document) =>
            enqueueDemoTask(() => {
                document.state = "processed";
                publishDocumentUpdate(document.id);
            }),
        );
};

export const clearDemoTimers = (): void => {
    pendingTimers.forEach((timer) => window.clearTimeout(timer));
    pendingTimers.clear();
};
