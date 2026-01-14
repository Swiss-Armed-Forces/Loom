import { configureStore, ThunkAction, AnyAction } from "@reduxjs/toolkit";
import commonReducer from "../features/common/commonSlice";
import searchReducer from "../features/search/searchSlice";
import archiveReducer from "../features/archives/archiveSlice";
import socketMiddleware from "../middleware/SocketMiddleware";
import SocketApi from "./api/socketApi";
import { localStorageCustomQueriesMiddleware } from "./middlewares";

export const store = configureStore({
    reducer: {
        common: commonReducer,
        search: searchReducer,
        archive: archiveReducer,
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware()
            .prepend(localStorageCustomQueriesMiddleware.middleware)
            .concat(socketMiddleware(new SocketApi())),
});

export type AppDispatch = typeof store.dispatch;
export type RootState = ReturnType<typeof store.getState>;
export type AppThunk<ReturnType = void> = ThunkAction<
    ReturnType,
    RootState,
    unknown,
    AnyAction
>;
