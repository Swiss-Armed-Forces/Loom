/**
 * Client-side reference counter for WebSocket channel subscriptions.
 *
 * The backend Redis pub/sub has no server-side ref-counting: a single
 * `unsubscribe` cancels the channel regardless of how many views have
 * subscribed. Multiple views (result cards, detail panel, folder tree) may
 * subscribe to the same file channel independently, so we track counts here
 * and only send the actual subscribe/unsubscribe to the server when the count
 * transitions between 0 and 1.
 */

import { Dispatch, UnknownAction } from "@reduxjs/toolkit";

import { webSocketSendMessage } from "@middleware/SocketMiddleware";

type DispatchFn = Dispatch<UnknownAction>;

const refCounts = new Map<string, number>();

export const subscribeChannel = (
    fileId: string,
    dispatch: DispatchFn,
): void => {
    const count = refCounts.get(fileId) ?? 0;
    refCounts.set(fileId, count + 1);
    if (count === 0) {
        dispatch(
            webSocketSendMessage({
                message: { type: "subscribe", channels: [fileId] },
            }),
        );
    }
};

export const unsubscribeChannel = (
    fileId: string,
    dispatch: DispatchFn,
): void => {
    const count = refCounts.get(fileId) ?? 0;
    if (count === 0) return;
    if (count === 1) {
        refCounts.delete(fileId);
        dispatch(
            webSocketSendMessage({
                message: { type: "unsubscribe", channels: [fileId] },
            }),
        );
    } else {
        refCounts.set(fileId, count - 1);
    }
};
