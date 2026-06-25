import { t } from "i18next";
import { toast } from "react-toastify";

import { PubSubMessage, PubSubMessageFromJSON } from "@app/api";
import SocketApi from "@app/api/socketApi";
import { setWebSocketPubSubMessage } from "@app/slices/searchSlice";
import { webSocket } from "@features/common/urls";

export const websocketConnect = { type: "webSocket/connect" };
export const webSocketSendMessage = (message: PubSubMessage) => ({
    type: "webSocket/send_message",
    message,
});
export const websocketDisconnect = { type: "webSocket/disconnect" };

const PING_INTERVAL_MS = 20_000;
const NOOP_PUB_SUB_MESSAGE: PubSubMessage = { message: { type: "noop" } };

const pingInterval: { id: ReturnType<typeof setInterval> | null } = {
    id: null,
};

const socketMiddleware =
    (socket: SocketApi) => (store: any) => (next: any) => (action: any) => {
        switch (action.type) {
            case "webSocket/connect":
                socket.connect(webSocket);
                socket.on("message", (event) => {
                    const webSocketPubSubMessage = PubSubMessageFromJSON(
                        JSON.parse(event.data),
                    );
                    store.dispatch(
                        setWebSocketPubSubMessage(webSocketPubSubMessage),
                    );
                });
                socket.on("open", () => {});
                socket.on("close", () => {
                    clearInterval(pingInterval.id ?? undefined);
                    pingInterval.id = null;
                    // Inform the user that the WebSocket connection has been closed.
                    toast.error(t("error.webSocketClosed"), {
                        toastId: "webSocketClosed",
                    });
                });
                pingInterval.id = setInterval(() => {
                    socket.send(NOOP_PUB_SUB_MESSAGE);
                }, PING_INTERVAL_MS);
                break;

            case "webSocket/send_message": {
                const message = action.message as PubSubMessage;
                socket.send(message);
                break;
            }

            case "webSocket/disconnect":
                clearInterval(pingInterval.id ?? undefined);
                pingInterval.id = null;
                socket.disconnect();
                break;
        }
        return next(action);
    };

export default socketMiddleware;
