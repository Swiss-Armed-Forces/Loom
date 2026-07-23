import {
    buildApiBasePath,
    buildWebSocketApiBasePath,
} from "@app/api/apiConfiguration";

import {
    DEMO_THUMBNAIL_FILE_ID,
    getArchives,
    getDocument,
    getRenderedAssetUrl,
} from "./repository";

const appUrl = new URL(import.meta.env.BASE_URL, window.location.origin);
const objectUrls = new Map<string, string>();

export const disposeDemoUrls = (): void => {
    objectUrls.forEach((url) => URL.revokeObjectURL(url));
    objectUrls.clear();
};

const objectUrl = (key: string, data: BlobPart, type: string): string => {
    const existing = objectUrls.get(key);
    if (existing) return existing;
    const url = URL.createObjectURL(new Blob([data], { type }));
    objectUrls.set(key, url);
    return url;
};

const serviceUrl = (): URL => new URL(appUrl);

export const thisUrl = new URL(window.location.href);
export const socketUrl = buildWebSocketApiBasePath(
    window.location.origin,
    import.meta.env.BASE_URL,
);
export const apiUrl = buildApiBasePath(
    window.location.origin,
    import.meta.env.BASE_URL,
);
export const webSocket = `${socketUrl}/v1/websocket`;

export const frontendHost = serviceUrl();
export const flowerHost = serviceUrl();
export const roundcubeHost = serviceUrl();
export const seaweedfsHost = serviceUrl();
export const s3Host = serviceUrl();
export const apiHost = serviceUrl();
export const rabbitHost = serviceUrl();
export const elasticSearchHost = serviceUrl();
export const elasticVueHost = serviceUrl();
export const rspamdHost = serviceUrl();
export const redisInsightHost = serviceUrl();
export const prometheusHost = serviceUrl();
export const grafanaHost = serviceUrl();
export const tikaHost = serviceUrl();
export const traefikHost = serviceUrl();
export const openWebuifrontendHost = serviceUrl();
export const ollamaHost = serviceUrl();
export const gotenbergHost = serviceUrl();

export const webApiGetFile = (fileId: string): string => {
    const document = getDocument(fileId);
    return document
        ? (document.downloadUrl ??
              objectUrl(`file-${fileId}`, document.data, document.mimeType))
        : "about:blank";
};
export const webApiGetFileOpen = webApiGetFile;
export const webApiGetFileThumbnail = (
    fileId: string,
    thumbnailFileId: string,
): string => {
    const document = getDocument(fileId);
    return document?.thumbnail && thumbnailFileId === DEMO_THUMBNAIL_FILE_ID
        ? document.thumbnail.url
        : "about:blank";
};
export const webApiGetFileRendered = (
    fileId: string,
    renderedId: string,
): string => {
    const document = getDocument(fileId);
    return document
        ? (getRenderedAssetUrl(document, renderedId) ?? "about:blank")
        : "about:blank";
};
export const webApiGetArchive = (fileId: string): string => {
    const archive = getArchives().find((item) => item.id === fileId);
    return archive
        ? objectUrl(
              `archive-${fileId}`,
              `Offline Loom archive: ${archive.name}\nQuery: ${archive.query}\n`,
              "application/zip",
          )
        : "about:blank";
};
export const webApiGetArchiveEncrypted = webApiGetArchive;
