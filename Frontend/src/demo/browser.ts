import { isCommonAssetRequest } from "msw";
import { setupWorker } from "msw/browser";

import { handlers } from "./handlers";

export const worker = setupWorker(...handlers);

export const startDemoWorker = async (): Promise<void> => {
    await worker.start({
        serviceWorker: {
            url: `${import.meta.env.BASE_URL}mockServiceWorker.js`,
        },
        onUnhandledRequest(request) {
            if (isCommonAssetRequest(request)) return;
            const url = new URL(request.url);
            if (
                url.origin === window.location.origin &&
                url.pathname.includes("/api/")
            )
                throw new Error(
                    `Unhandled demo API route: ${request.method} ${url.pathname}`,
                );
        },
    });
};
