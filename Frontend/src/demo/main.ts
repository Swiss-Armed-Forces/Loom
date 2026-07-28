import { startDemoWorker } from "./browser";
import { resetDemoHandlerState } from "./handlers";
import { clearDemoTimers, resetDemoRepository } from "./repository";
import { seedDemoSavedQuery } from "./savedQuery";
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

seedDemoSavedQuery(window.localStorage);
await import("../main");
