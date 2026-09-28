import { createAction, createListenerMiddleware } from "@reduxjs/toolkit";

import { fetchFilesCountForCustomQuery } from "@app/slices/searchSlice";
import {
    websocketConnect,
    websocketDisconnect,
} from "@middleware/SocketMiddleware";

import { RootState } from "../store";

export const SAVED_QUERY_COUNT_POLL_INTERVAL_MS = 30_000;

/**
 * Refresh the match count of every saved query.
 *
 * This is the seam the polling loop pushes against. When saved-query evaluation
 * moves server-side, the loop below is deleted and a websocket message handler
 * dispatches this instead — nothing else has to change.
 */
export const refreshSavedQueryCounts = createAction(
    "savedQueries/refreshCounts",
);

/**
 * Store-level polling for saved-query match counts.
 *
 * Polling used to live in a `setInterval` inside `CustomQueryItem`, which is
 * only mounted while the left sidebar shows the QUERIES panel — so the activity
 * bar badge it feeds could never light up unless the user already had the panel
 * open. Owning the timer at the store level decouples it from the view tree.
 *
 * Its own middleware instance rather than a listener on
 * `localStorageSearchStateMiddleware`: `clearListeners()` is per-instance, so
 * sharing one would force the tests here to either run against the live
 * localStorage persist listener or tear it down.
 */
export const createSavedQueryListenerMiddleware = () => {
    const middleware = createListenerMiddleware();
    // Guards against rounds stacking up if the backend is slower than the poll
    // interval. Closure-scoped so each instance (and so each test) is isolated.
    let roundInFlight = false;

    middleware.startListening({
        actionCreator: refreshSavedQueryCounts,
        effect: async (_action, listenerApi) => {
            if (roundInFlight) return;
            roundInFlight = true;
            try {
                // Read the ids fresh every round so queries added or deleted
                // mid-session are picked up without restarting the loop.
                const customQueryIds = (
                    listenerApi.getState() as RootState
                ).search.customQueries.map((customQuery) => customQuery.id);
                for (const customQueryId of customQueryIds) {
                    // Sequential: the per-item intervals this replaces were
                    // accidentally staggered, and firing N requests at once
                    // would be a regression. The thunk rejects rather than
                    // throws, so one failure cannot abort the round.
                    await listenerApi.dispatch(
                        fetchFilesCountForCustomQuery({ customQueryId }),
                    );
                }
            } finally {
                roundInFlight = false;
            }
        },
    });

    // One entry matching both lifecycle actions, so the disconnect branch can
    // cancel the loop started by the connect branch. Repeated connects are
    // idempotent, which matters because StrictMode double-runs the effect that
    // dispatches them and the ordering is not guaranteed.
    middleware.startListening({
        predicate: (action) =>
            action.type === websocketConnect.type ||
            action.type === websocketDisconnect.type,
        effect: async (action, listenerApi) => {
            listenerApi.cancelActiveListeners();
            if (action.type === websocketDisconnect.type) return;

            const onVisibilityChange = () => {
                if (!document.hidden) {
                    listenerApi.dispatch(refreshSavedQueryCounts());
                }
            };
            document.addEventListener("visibilitychange", onVisibilityChange);
            try {
                for (;;) {
                    await listenerApi.delay(SAVED_QUERY_COUNT_POLL_INTERVAL_MS);
                    // Skip the tick rather than stopping the loop; the
                    // visibilitychange handler above covers the catch-up.
                    if (document.hidden) continue;
                    listenerApi.dispatch(refreshSavedQueryCounts());
                }
            } finally {
                // Reached via TaskAbortError when cancelActiveListeners()
                // aborts the pending delay.
                document.removeEventListener(
                    "visibilitychange",
                    onVisibilityChange,
                );
            }
        },
    });

    return middleware;
};

export const savedQueryListenerMiddleware =
    createSavedQueryListenerMiddleware();
