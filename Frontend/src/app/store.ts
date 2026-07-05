import { configureStore, ThunkAction, UnknownAction } from "@reduxjs/toolkit";

import archiveReducer from "@app/slices/archiveSlice";
import commonReducer from "@app/slices/commonSlice";
import searchReducer from "@app/slices/searchSlice";

import socketMiddleware from "../middleware/SocketMiddleware";

import SocketApi from "./api/socketApi";
import {
    localStorageAutoActionsMiddleware,
    localStorageCustomQueriesMiddleware,
    localStorageUiStateMiddleware,
} from "./middlewares";

export const store = configureStore({
    reducer: {
        common: commonReducer,
        search: searchReducer,
        archive: archiveReducer,
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware()
            .prepend(localStorageCustomQueriesMiddleware.middleware)
            .prepend(localStorageAutoActionsMiddleware.middleware)
            .prepend(localStorageUiStateMiddleware.middleware)
            .concat(socketMiddleware(new SocketApi())),
});

export type AppDispatch = typeof store.dispatch;
export type RootState = ReturnType<typeof store.getState>;
export type AppThunk<ReturnType = void> = ThunkAction<
    ReturnType,
    RootState,
    unknown,
    UnknownAction
>;
