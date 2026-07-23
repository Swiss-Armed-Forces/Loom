import { startDemoWorker } from "./browser";
import { resetDemoHandlerState } from "./handlers";
import { clearDemoTimers, resetDemoRepository } from "./repository";
import { disposeDemoUrls } from "./urls";

resetDemoRepository();
resetDemoHandlerState();
await startDemoWorker();

window.addEventListener(
    "pagehide",
    () => {
        clearDemoTimers();
        resetDemoHandlerState();
        disposeDemoUrls();
    },
    { once: true },
);

const basePath = import.meta.env.BASE_URL.replace(/\/$/, "");
if (
    window.location.pathname === `${basePath}/` ||
    window.location.pathname === basePath
) {
    window.history.replaceState({}, "", `${basePath}/search?query=*`);
}

await import("../main");
