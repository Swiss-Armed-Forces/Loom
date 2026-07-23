import { ws } from "msw";

import { addClient, removeClient, subscribe, unsubscribe } from "./channels";
import { objectValue, stringArrayValue } from "./shared";

const apiSocket = ws.link(/\/api\/v1\/websocket$/);

export const socketHandler = apiSocket.addEventListener(
    "connection",
    ({ client }) => {
        const socket = client as unknown as WebSocket;
        addClient(socket);
        client.addEventListener("message", (event) => {
            // Prevent MSW from forwarding keepalives or unknown messages to a
            // backend that deliberately does not exist in demo mode.
            event.preventDefault();
            try {
                const payload: unknown = JSON.parse(String(event.data));
                const payloadObject = objectValue(payload);
                const message =
                    objectValue(payloadObject?.message) ?? payloadObject;
                if (!message || typeof message.type !== "string")
                    throw new Error("Invalid message");
                const channels = stringArrayValue(message.channels) ?? [];
                switch (message.type) {
                    case "noop":
                        return;
                    case "subscribe":
                        subscribe(socket, channels);
                        client.send(
                            JSON.stringify({
                                message: {
                                    type: "subscribeConfirmation",
                                    channels,
                                },
                            }),
                        );
                        return;
                    case "unsubscribe":
                        unsubscribe(socket, channels);
                        client.send(
                            JSON.stringify({
                                message: {
                                    type: "unsubscribeConfirmation",
                                    channels,
                                },
                            }),
                        );
                        return;
                    default:
                        throw new Error("Unsupported message type");
                }
            } catch {
                client.send(
                    JSON.stringify({
                        message: {
                            type: "error",
                            message: "Invalid demo socket message",
                        },
                    }),
                );
            }
        });
        client.addEventListener("close", () => removeClient(socket));
    },
);
