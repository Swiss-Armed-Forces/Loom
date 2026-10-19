import { configureStore, ThunkAction, UnknownAction } from "@reduxjs/toolkit";

import archiveReducer from "@app/slices/archiveSlice";
import commonReducer from "@app/slices/commonSlice";
import searchReducer from "@app/slices/searchSlice";

import socketMiddleware from "../middleware/SocketMiddleware";

import SocketApi from "./api/socketApi";
import { savedQueryListenerMiddleware } from "./listeners/savedQueryListener";
import { localStorageSearchStateMiddleware } from "./middlewares";

export const store = configureStore({
    reducer: {
        common: commonReducer,
        search: searchReducer,
        archive: archiveReducer,
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
            // Both checks are development-only and walk the state tree on every
            // dispatched action. `search.files` holds a full preview per result
            // — tags, attachments, highlight fragments and the extracted text
            // of every selected field — so walking it is what made them
            // expensive. Everything else stays covered.
            serializableCheck: {
                // Channel subscriptions carry a Set. The message rides on the
                // action's own `message` key rather than under `payload`, so it
                // is the action that has to be exempted, by its real type:
                // SocketMiddleware dispatches "webSocket/send_message", and it
                // already converts inbound Sets to arrays before they reach a
                // reducer.
                ignoredActions: ["webSocket/send_message"],
                ignoredPaths: ["search.files"],
            },
            immutableCheck: {
                ignoredPaths: ["search.files"],
            },
        })
            .prepend(localStorageSearchStateMiddleware.middleware)
            .prepend(savedQueryListenerMiddleware.middleware)
            .concat(socketMiddleware(new SocketApi())),
});

export type AppStore = typeof store;
export type AppDispatch = typeof store.dispatch;
export type RootState = ReturnType<typeof store.getState>;
export type AppThunk<ReturnType = void> = ThunkAction<
    ReturnType,
    RootState,
    unknown,
    UnknownAction
>;
