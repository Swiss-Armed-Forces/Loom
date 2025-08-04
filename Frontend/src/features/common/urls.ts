export const thisUrl = new URL(window.location.href);

/// Use TLS except if env TLS_ENABLED is false
const isHttps = window.location.protocol === "https:";
const wsProtocol = isHttps ? "wss" : "ws";
const apiProtocol = isHttps ? "https" : "http";

export const socketUrl = `${wsProtocol}://${window.location.hostname}/api`;
export const apiUrl = `${apiProtocol}://${window.location.hostname}/api`;

function getHost(host: string): URL {
    const urlCopy = new URL(thisUrl);
    if (!urlCopy.hostname.includes("frontend")) {
        urlCopy.hostname = `frontend.${urlCopy.hostname}`;
    }
    urlCopy.hostname = urlCopy.hostname.replace("frontend", host);
    urlCopy.pathname = "";
    urlCopy.search = "";
    urlCopy.hash = "";
    return urlCopy;
}

export const flowerHost = getHost("flower");
export const translateHost = getHost("translate");
export const roundcubeHost = getHost("roundcube");
export const minioHost = getHost("minio");
export const apiHost = getHost("api");
export const rabbitHost = getHost("rabbit");
export const elasticSearchHost = getHost("elasticsearch");
export const elasticVueHost = getHost("elasticvue");
export const mongoWebHost = getHost("mongo-web");
export const rspamdHost = getHost("rspamd");
export const redisInsightHost = getHost("redisinsight");
export const prometheusHost = getHost("prometheus");
export const grafanaHost = getHost("grafana");
export const tikaHost = getHost("tika");
export const traefikHost = getHost("traefik");
export const openWebuifrontendHost = getHost("open-webui");
export const ollamaHost = getHost("ollama");

export const webApiGetFile = (fileId: string) =>
    `${apiUrl}/v1/files/${fileId}/download`;
export const webApiGetFileText = (fileId: string) =>
    `${apiUrl}/v1/files/${fileId}/text`;
export const webApiGetFileThumbnail = (file_id: string) =>
    `${apiUrl}/v1/files/${file_id}/thumbnail`;
export const webApiGetFilePreview = (file_id: string) =>
    `${apiUrl}/v1/files/${file_id}/thumbnail?preview=true`;
export const webApiGetArchive = (fileId: string) =>
    `${apiUrl}/v1/archive/${fileId}`;
export const webApiGetArchiveEncrypted = (fileId: string) =>
    `${apiUrl}/v1/archive/${fileId}?encrypted=true`;

export const webSocket = `${socketUrl}/v1/websocket`;
