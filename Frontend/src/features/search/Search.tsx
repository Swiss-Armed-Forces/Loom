import { t } from "i18next";
import { useEffect, useRef } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "react-toastify";

import {
    loadTags,
    MessageFileUpdate,
    loadSummarizationSystemPrompt,
    loadVisionSystemPrompt,
    MessageQueryIdExpired,
    MessageError,
} from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    startLoadingIndicator,
    stopLoadingIndicator,
} from "@app/slices/commonSlice";
import {
    fetchPreview,
    openFileTabThunk,
    selectActiveTabFileId,
    selectFiles,
    selectPushHistory,
    selectWebSocketPubSubMessage,
    setActiveTabFileId,
    setPushHistory,
    updateQuery,
    setSummarizationSystemPrompt,
    setVisionSystemPrompt,
    setTags,
    selectQuery,
} from "@app/slices/searchSlice";
import { ActivityBar } from "@features/search/components/ActivityBar/ActivityBar";
import { CenterTabs } from "@features/search/components/CenterTabs/CenterTabs";
import { LeftSidebar } from "@features/search/components/LeftSidebar/LeftSidebar";
import { RightSidebar } from "@features/search/components/RightSidebar/RightSidebar";
import { useKeyboardNavigation } from "@features/search/hooks/useKeyboardNavigation";

import {
    websocketConnect,
    websocketDisconnect,
} from "../../middleware/SocketMiddleware";
import { isSortDirection, SearchQuery } from "../common/utils/model";

import styles from "./Search.module.css";

const RELOAD_TIMEOUT_MS = 5_000;
const UPDATE_QUERY_DEBOUNCE_MS = 2_000;

export const Search = () => {
    const dispatch = useAppDispatch();
    const navigate = useNavigate();
    const location = useLocation();
    const searchQuery = useAppSelector(selectQuery);
    const webSocketPubSubMessage = useAppSelector(selectWebSocketPubSubMessage);
    const files = useAppSelector(selectFiles);
    const activeTabFileId = useAppSelector(selectActiveTabFileId);
    const pushHistory = useAppSelector(selectPushHistory);
    // Avoid adding pushHistory to the URL-sync effect's dep array
    const pushHistoryRef = useRef(false);
    // Prevent feedback loops between hash→Redux and Redux→hash effects.
    // Initialized to "" (not location.hash) so the URL→Redux effect processes
    // the initial hash on mount rather than skipping it. The initial
    // activeTabFileId is seeded from the URL hash in Redux initialState, so
    // the Redux→URL effect returns early on mount without clearing the hash.
    const syncedHashRef = useRef<string>("");

    // Initialize keyboard navigation
    useKeyboardNavigation();

    const [searchParams] = useSearchParams();

    const updateQueryDebounceTimeoutRef = useRef<ReturnType<
        typeof setTimeout
    > | null>(null);

    useEffect(() => {
        const fetchSearchState = async () => {
            try {
                const tags = await loadTags();
                dispatch(setTags(tags));
            } catch (error) {
                toast.error(`Error in fetchSearchState: ${error}`);
            }
        };

        const fetchInitialSearchState = async () => {
            dispatch(startLoadingIndicator());
            try {
                const [prompt, visionPrompt] = await Promise.all([
                    loadSummarizationSystemPrompt(),
                    loadVisionSystemPrompt(),
                ]);
                dispatch(setSummarizationSystemPrompt(prompt));
                dispatch(setVisionSystemPrompt(visionPrompt));
                await fetchSearchState();
                dispatch(websocketConnect);
            } catch (error) {
                toast.error(`Error in fetchInitialSearchState: ${error}`);
            } finally {
                dispatch(stopLoadingIndicator());
            }
        };

        fetchInitialSearchState();

        // refresh search state after timeout
        const fetchSearchStateInterval = setInterval(
            fetchSearchState,
            RELOAD_TIMEOUT_MS,
        );

        return () => {
            clearInterval(fetchSearchStateInterval);
            dispatch(websocketDisconnect);
        };
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    // URL → Redux: sync search params into Redux state.
    // Runs on every searchParams change (not just initial load) so that
    // Back/Forward navigation updates the search results accordingly.
    // The equality guard prevents the Redux→URL→Redux feedback loop.
    useEffect(() => {
        const query = searchParams.get("query") ?? "";
        const sortField = searchParams.get("sortField") ?? undefined;
        const sortDirection = searchParams.get("sortDirection");
        const urlSortDirection =
            sortDirection !== null && isSortDirection(sortDirection)
                ? sortDirection
                : undefined;

        // No-op when Redux already reflects the URL (avoids loop after
        // the Redux→URL effect writes the same params back)
        if (
            searchQuery &&
            (searchQuery.query ?? "") === query &&
            (searchQuery.sortField ?? undefined) === sortField &&
            (searchQuery.sortDirection ?? undefined) === urlSortDirection
        )
            return;

        dispatch(
            updateQuery({
                query: query || undefined,
                sortField: sortField,
                sortDirection: urlSortDirection,
            }),
        );
    }, [searchParams]); // eslint-disable-line react-hooks/exhaustive-deps

    // Keep pushHistoryRef in sync so the URL-sync effect can read it without
    // adding it to the dependency array (which would cause extra re-runs).
    useEffect(() => {
        pushHistoryRef.current = pushHistory;
    }, [pushHistory]);

    // Redux → URL hash: navigate when the active tab changes.
    // Push a new history entry when opening the first tab (null → fileId) so
    // Back returns to the results view; replace for all other transitions.
    useEffect(() => {
        const targetHash = activeTabFileId ? `#${activeTabFileId}` : "";
        if (location.hash === targetHash) return;

        syncedHashRef.current = targetHash;
        const shouldPush = activeTabFileId !== null;
        navigate(
            {
                pathname: location.pathname,
                search: location.search,
                hash: activeTabFileId ?? "",
            },
            { replace: !shouldPush },
        );
    }, [activeTabFileId]); // eslint-disable-line react-hooks/exhaustive-deps

    // URL hash → Redux: open or switch to the file tab when the hash changes
    // (covers initial page load, Back/Forward, and direct URL pasting).
    useEffect(() => {
        const fileId = location.hash.substring(1);
        if (syncedHashRef.current === location.hash) return;
        // Always keep the ref in sync so Forward navigation is not skipped
        // after Back resets the ref to an earlier value.
        syncedHashRef.current = location.hash;
        if (!fileId) {
            dispatch(setActiveTabFileId(null));
            return;
        }
        dispatch(openFileTabThunk({ fileId }));
    }, [location.hash]); // eslint-disable-line react-hooks/exhaustive-deps

    // persist search state in URL query params
    useEffect(() => {
        if (!searchQuery) return;

        const params = new URLSearchParams();
        const fields: (keyof SearchQuery)[] = [
            "query",
            "sortField",
            "sortDirection",
        ];

        fields.forEach((field) => {
            const value = searchQuery[field];
            if (value) params.set(field as string, String(value));
        });

        // Push a new history entry for committed user actions (Enter, sort
        // toggle, custom query click), replace for all programmatic updates.
        // Use navigate (not setSearchParams) to preserve the hash — React
        // Router's setSearchParams navigates to "?..." which clears the hash.
        const shouldReplace = !pushHistoryRef.current;
        if (pushHistoryRef.current) dispatch(setPushHistory(false));
        navigate(
            {
                pathname: location.pathname,
                search: params.toString(),
                hash: location.hash,
            },
            { replace: shouldReplace },
        );
    }, [searchQuery]); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        if (!webSocketPubSubMessage) return;
        const { message } = webSocketPubSubMessage;

        switch (message.type) {
            case "error":
                toast.error((message as MessageError).message);
                break;

            case "fileUpdate": {
                // Only refresh preview for files currently in the search
                // result set. fileUpdate messages may also arrive for files
                // subscribed by the folder tree view.
                const { fileId } = message as MessageFileUpdate;
                if (fileId in files) {
                    dispatch(fetchPreview({ fileId }));
                }
                break;
            }
        }
    }, [webSocketPubSubMessage, files]); // eslint-disable-line react-hooks/exhaustive-deps

    // update query id and show toast
    useEffect(() => {
        const message =
            webSocketPubSubMessage?.message as MessageQueryIdExpired;
        if (message?.type !== "queryIdExpired") return;
        const oldQueryId = message.oldId;
        if (searchQuery?.id !== oldQueryId) return;

        if (updateQueryDebounceTimeoutRef.current)
            clearTimeout(updateQueryDebounceTimeoutRef.current);

        updateQueryDebounceTimeoutRef.current = setTimeout(() => {
            dispatch(updateQuery({ id: message.newId }));
            toast.info(t("generalSearchView.queryExpired"));
            updateQueryDebounceTimeoutRef.current = null;
        }, UPDATE_QUERY_DEBOUNCE_MS);

        return () => {
            if (updateQueryDebounceTimeoutRef.current) {
                clearTimeout(updateQueryDebounceTimeoutRef.current);
            }
        };
    }, [webSocketPubSubMessage, searchQuery?.id]); // eslint-disable-line react-hooks/exhaustive-deps

    return (
        <div className={styles.searchWrapper}>
            <ActivityBar />
            <LeftSidebar />
            <div className={styles.mainContent}>
                <CenterTabs />
            </div>
            <RightSidebar />
        </div>
    );
};
