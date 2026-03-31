import { toast } from "react-toastify";
import { PubSubMessage, PubSubMessageFromJSON } from "../app/api";
import SocketApi from "../app/api/socketApi";
import { webSocket } from "../features/common/urls";
import { setWebSocketPubSubMessage } from "../features/search/searchSlice";
import { t } from "i18next";

export const websocketConnect = { type: "webSocket/connect" };
export const webSocketSendMessage = (message: PubSubMessage) => ({
    type: "webSocket/send_message",
    message,
});
export const websocketDisconnect = { type: "webSocket/disconnect" };

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
                    // Inform the user that the WebSocket connection has been closed.
                    toast.error(t("error.webSocketClosed"), {
                        toastId: "webSocketClosed",
                    });
                });
                break;

            case "webSocket/send_message": {
                const message = action.message as PubSubMessage;
                socket.send(message);
                break;
            }

            case "webSocket/disconnect":
                socket.disconnect();
                break;
        }
        return next(action);
    };

export default socketMiddleware;
