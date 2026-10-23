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

/**
 * How long a channel is kept after the last view of it goes away.
 *
 * Cards subscribe when they scroll into view and release when they leave, so
 * a fast scroll used to send a subscribe and an unsubscribe for every row it
 * passed - measured at about sixty-four a second, each one a `SUBSCRIBE` and
 * an `UNSUBSCRIBE` against Redis for a file nobody stopped to read. Holding
 * the channel briefly means a row scrolled past and back costs nothing, and a
 * row genuinely left behind is released a moment later.
 */
const RELEASE_GRACE_MS = 3_000;

const pendingRelease = new Map<string, ReturnType<typeof setTimeout>>();

const cancelPendingRelease = (fileId: string): boolean => {
    const timer = pendingRelease.get(fileId);
    if (timer === undefined) return false;
    clearTimeout(timer);
    pendingRelease.delete(fileId);
    return true;
};

export const subscribeChannel = (
    fileId: string,
    dispatch: DispatchFn,
): void => {
    const count = refCounts.get(fileId) ?? 0;
    refCounts.set(fileId, count + 1);
    // Still subscribed, just on its way out: take it back rather than
    // re-subscribing to a channel that was never dropped.
    if (cancelPendingRelease(fileId)) return;
    if (count === 0) {
        dispatch(
            webSocketSendMessage({
                message: { type: "subscribe", channels: new Set([fileId]) },
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
    if (count > 1) {
        refCounts.set(fileId, count - 1);
        return;
    }
    refCounts.delete(fileId);
    if (pendingRelease.has(fileId)) return;
    pendingRelease.set(
        fileId,
        setTimeout(() => {
            pendingRelease.delete(fileId);
            // Taken back in the meantime: `subscribeChannel` cancels the timer,
            // so reaching here means nothing did.
            dispatch(
                webSocketSendMessage({
                    message: {
                        type: "unsubscribe",
                        channels: new Set([fileId]),
                    },
                }),
            );
        }, RELEASE_GRACE_MS),
    );
};

/** Drop every channel and every pending release. For tests and teardown. */
export const resetChannelSubscriptions = (): void => {
    for (const timer of pendingRelease.values()) clearTimeout(timer);
    pendingRelease.clear();
    refCounts.clear();
};
