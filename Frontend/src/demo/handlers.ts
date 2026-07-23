import { http } from "msw";

import { aiHandlers, resetAiState } from "./handlers/ai";
import { archiveHandlers } from "./handlers/archives";
import { resetChannels, sendToChannel } from "./handlers/channels";
import { filesHandlers } from "./handlers/files";
import { error } from "./handlers/shared";
import { systemHandlers } from "./handlers/system";
import { socketHandler } from "./handlers/websocket";
import { setDemoDocumentUpdatePublisher } from "./repository";

const unhandledApiHandler = http.all(/\/api\/v1\/.*/, ({ request }) =>
    error(`Unhandled demo API route: ${request.method}`, 501),
);

setDemoDocumentUpdatePublisher((fileId) =>
    sendToChannel(fileId, { type: "fileUpdate", fileId }),
);

export const resetDemoHandlerState = (): void => {
    resetAiState();
    resetChannels();
};

export const handlers = [
    ...systemHandlers,
    ...filesHandlers,
    ...archiveHandlers,
    ...aiHandlers,
    socketHandler,
    unhandledApiHandler,
];
