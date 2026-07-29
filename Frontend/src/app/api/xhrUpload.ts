import { apiConfiguration } from "./apiConfiguration";

export const xhrUpload = (
    path: string,
    file: File,
    onProgress: (percent: number) => void,
    signal?: AbortSignal,
): Promise<void> =>
    new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                onProgress(Math.round((event.loaded / event.total) * 100));
            }
        };

        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve();
            } else {
                reject(
                    new Error(
                        `${xhr.status}: ${xhr.statusText || "Upload failed"}`,
                    ),
                );
            }
        };

        xhr.onerror = () => reject(new Error("Upload failed"));

        xhr.onabort = () =>
            reject(new DOMException("Upload aborted", "AbortError"));

        if (signal) {
            signal.addEventListener("abort", () => xhr.abort());
        }

        const formData = new FormData();
        formData.append("file", file);
        xhr.open("POST", `${apiConfiguration.basePath}${path}`);
        xhr.send(formData);
    });
