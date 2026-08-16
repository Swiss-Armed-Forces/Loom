import { t } from "i18next";
import { toast } from "react-toastify";

import {
    PubSubMessage,
    PubSubMessageFromJSON,
    PubSubMessageToJSON,
} from "@app/api";
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

let intentionalDisconnect = false;
window.addEventListener("beforeunload", () => {
    intentionalDisconnect = true;
});

const socketMiddleware =
    (socket: SocketApi) => (store: any) => (next: any) => (action: any) => {
        switch (action.type) {
            case "webSocket/connect":
                if (pingInterval.id !== null) break;
                socket.connect(webSocket);
                socket.on("message", (event) => {
                    const webSocketPubSubMessage = PubSubMessageFromJSON(
                        JSON.parse(event.data),
                    );
                    // Convert any Set fields to arrays before dispatching
                    // into the Redux store (the OpenAPI generator produces
                    // Set<string> for uniqueItems arrays, which is not
                    // serializable).
                    const msg = webSocketPubSubMessage.message;
                    if ("channels" in msg && msg.channels instanceof Set) {
                        msg.channels = [...msg.channels] as any;
                    }
                    store.dispatch(
                        setWebSocketPubSubMessage(webSocketPubSubMessage),
                    );
                });
                socket.on("close", () => {
                    clearInterval(pingInterval.id ?? undefined);
                    pingInterval.id = null;
                    socket.disconnect();
                    if (!intentionalDisconnect) {
                        toast.error(t("error.webSocketClosed"), {
                            toastId: "webSocketClosed",
                        });
                    }
                    intentionalDisconnect = false;
                });
                pingInterval.id = setInterval(() => {
                    socket.send(NOOP_PUB_SUB_MESSAGE);
                }, PING_INTERVAL_MS);
                break;

            case "webSocket/send_message": {
                const message = action.message as PubSubMessage;
                socket.send(PubSubMessageToJSON(message));
                return;
            }

            case "webSocket/disconnect":
                intentionalDisconnect = true;
                clearInterval(pingInterval.id ?? undefined);
                pingInterval.id = null;
                socket.disconnect();
                break;
        }
        return next(action);
    };

export default socketMiddleware;
