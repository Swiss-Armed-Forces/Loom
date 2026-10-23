import { useMediaQuery } from "@mui/material";
import { useEffect, useRef } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "react-toastify";

import {
    loadTags,
    MessageFileUpdate,
    loadSummarizationSystemPrompt,
    loadVisionSystemPrompt,
    MessageError,
} from "@app/api";
import { useAppDispatch, useAppSelector, useAppStore } from "@app/hooks";
import {
    startLoadingIndicator,
    stopLoadingIndicator,
} from "@app/slices/commonSlice";
import {
    fetchPreview,
    openFileTabThunk,
    selectFileDetailSelection,
    selectWebSocketPubSubMessage,
    focusFollowTab,
    updateQuery,
    setSummarizationSystemPrompt,
    setVisionSystemPrompt,
    setTags,
    selectQuery,
    closeLeftSidebar,
    closeRightSidebar,
} from "@app/slices/searchSlice";
import { ActivityBar } from "@features/search/components/ActivityBar/ActivityBar";
import { LeftSidebar } from "@features/search/components/LeftSidebar/LeftSidebar";
import { RightSidebar } from "@features/search/components/RightSidebar/RightSidebar";
import { useKeyboardNavigation } from "@features/search/hooks/useKeyboardNavigation";
import { useOpenFileTabSubscriptions } from "@features/search/hooks/useOpenFileTabSubscriptions";
import { SearchResults } from "@features/search/views/SearchResults/SearchResults";

import {
    websocketConnect,
    websocketDisconnect,
    webSocketSendMessage,
} from "../../middleware/SocketMiddleware";
import { isSortDirection, SearchQuery } from "../common/utils/model";

import styles from "./Search.module.css";

export const Search = () => {
    const dispatch = useAppDispatch();
    const navigate = useNavigate();
    const location = useLocation();
    const searchQuery = useAppSelector(selectQuery);
    const isMobile = useMediaQuery("(max-width:600px)");
    const webSocketPubSubMessage = useAppSelector(selectWebSocketPubSubMessage);
    const selection = useAppSelector(selectFileDetailSelection);
    // Prevent feedback loops between hash→Redux and Redux→hash effects.
    // Initialized to "" (not location.hash) so the URL→Redux effect processes
    // the initial hash on mount rather than skipping it. The initial
    // selection is seeded from the URL hash in Redux initialState, so the
    // Redux→URL effect returns early on mount without clearing the hash.
    const syncedHashRef = useRef<string>("");
    // The file cache is only read inside the WS handler below. Subscribing to it
    // would re-render the whole search page on every preview that arrives, which
    // is why this reads the store rather than keeping a ref fed by a selector.
    const store = useAppStore();
    // The search string the Redux→URL effect last wrote. The URL→Redux effect
    // skips exactly that one value, which is what breaks the feedback loop
    // between the two without also swallowing a URL the user arrived with.
    // Initialized to null so no real location.search can match it on mount.
    const syncedSearchRef = useRef<string | null>(null);
    // Whether the URL→Redux effect has seen the URL the page was opened with.
    // Only that first one may re-run a query restored from localStorage.
    const initialUrlSyncDoneRef = useRef(false);
    // Guards the Redux→URL effect: its mount run writes nothing, and the first
    // write it does make replaces the entry the page was opened with.
    const isFirstUrlWriteRenderRef = useRef(true);
    const hasWrittenUrlRef = useRef(false);
    // Read inside the URL→Redux effect, which must not re-run when the query
    // changes - running it again on a Redux change is the loop it guards.
    const searchQueryRef = useRef(searchQuery);
    searchQueryRef.current = searchQuery;

    // Initialize keyboard navigation
    useKeyboardNavigation();
    // Tabs are subscribed from here rather than from their panels, which only
    // exist while the File Detail pane is the one on screen.
    useOpenFileTabSubscriptions();

    const [searchParams] = useSearchParams();

    const isFirstQueryRenderRef = useRef(true);
    useEffect(() => {
        if (isFirstQueryRenderRef.current) {
            isFirstQueryRenderRef.current = false;
            return;
        }
        if (!isMobile) return;
        dispatch(closeLeftSidebar());
        dispatch(closeRightSidebar());
    }, [searchQuery?.query]); // eslint-disable-line react-hooks/exhaustive-deps

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
                // If the Redux state already holds a cached query (restored from
                // localStorage), subscribe its WS channel immediately so we receive
                // fileUpdate messages without a full re-fetch.
                // SocketApi queues this until the connection is open.
                if (searchQuery?.id) {
                    dispatch(
                        webSocketSendMessage({
                            message: {
                                type: "subscribe",
                                channels: new Set([searchQuery.id]),
                            },
                        }),
                    );
                }
            } catch (error) {
                toast.error(`Error in fetchInitialSearchState: ${error}`);
            } finally {
                dispatch(stopLoadingIndicator());
            }
        };

        fetchInitialSearchState();

        return () => {
            dispatch(websocketDisconnect);
        };
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    // URL → Redux: run the search the URL describes.
    // Runs on every location.search change (not just initial load) so that
    // Back/Forward navigation updates the search results accordingly, and on
    // the search string rather than the searchParams object, whose identity
    // also changes on a hash-only navigation.
    //
    // A URL carrying ?query= is searched every time it arrives, including on
    // first load. Matching it against Redux would not do: the query is
    // restored from localStorage while the results are not, so a reloaded or
    // shared URL would fill the fields and show nothing.
    useEffect(() => {
        // Our own write, already in Redux - taking it for a navigation is the
        // Redux→URL→Redux loop.
        if (location.search === syncedSearchRef.current) return;
        syncedSearchRef.current = location.search;
        const isInitialSync = !initialUrlSyncDoneRef.current;
        initialUrlSyncDoneRef.current = true;

        const urlQuery = searchParams.get("query");
        if (urlQuery === null) {
            // No query in the URL. On arrival, re-run the one restored from
            // localStorage so the search fields and the results agree; a later
            // param-less navigation leaves Redux alone. updateQuery falls back
            // to the last query for every field it is not given.
            if (isInitialSync && searchQueryRef.current?.query) {
                dispatch(updateQuery({}));
            }
            return;
        }

        const sortDirection = searchParams.get("sortDirection");
        // A URL that names a query describes the whole search, so a sort it
        // does not name is no sort - passing null rather than undefined is
        // what keeps the reader's own sort out of a shared link.
        dispatch(
            updateQuery({
                query: urlQuery || undefined,
                sortField: searchParams.get("sortField"),
                sortDirection:
                    sortDirection !== null && isSortDirection(sortDirection)
                        ? sortDirection
                        : null,
            }),
        );
    }, [location.search]); // eslint-disable-line react-hooks/exhaustive-deps

    // Redux → URL hash: navigate when the selected File Detail tab changes.
    //
    // The hash names an opened tab. The following tab has none: its file is
    // the highlight, so writing it would mean a `navigate` per arrow key.
    //
    // Push a new history entry when opening the first tab (no hash → fileId)
    // so Back returns to the results; replace for all other transitions.
    useEffect(() => {
        const targetHash =
            selection.kind === "file" ? `#${selection.fileId}` : "";
        if (location.hash === targetHash) return;

        const shouldPush = targetHash !== "" && syncedHashRef.current === "";
        syncedHashRef.current = targetHash;
        navigate(
            {
                pathname: location.pathname,
                search: location.search,
                hash: targetHash.substring(1),
            },
            { replace: !shouldPush },
        );
    }, [selection]); // eslint-disable-line react-hooks/exhaustive-deps

    // URL hash → Redux: open or switch to the file tab when the hash changes
    // (covers initial page load, Back/Forward, and direct URL pasting).
    useEffect(() => {
        const fileId = location.hash.substring(1);
        if (syncedHashRef.current === location.hash) return;
        // Always keep the ref in sync so Forward navigation is not skipped
        // after Back resets the ref to an earlier value.
        syncedHashRef.current = location.hash;
        if (!fileId) {
            dispatch(focusFollowTab());
            return;
        }
        dispatch(openFileTabThunk({ fileId }));
    }, [location.hash]); // eslint-disable-line react-hooks/exhaustive-deps

    // Redux → URL: persist search state in URL query params.
    // Skips navigate when the URL already reflects the current state (avoids
    // the Redux→URL→Redux feedback loop on Back/Forward and initial load).
    // Pushes a new history entry when the URL actually changes so that every
    // query/sort interaction is navigable via Back/Forward - except for the
    // first write, which only spells out what the page was opened with and
    // would otherwise leave Back pointing at a URL describing no search.
    // Use navigate (not setSearchParams) to preserve the hash — React
    // Router's setSearchParams navigates to "?..." which clears the hash.
    //
    // The mount run is skipped entirely: on arrival the URL is what the user
    // asked for, and writing the query restored from localStorage over it
    // would replace a shared link before it is read.
    useEffect(() => {
        if (isFirstUrlWriteRenderRef.current) {
            isFirstUrlWriteRenderRef.current = false;
            return;
        }
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

        const newSearch = params.toString() ? `?${params.toString()}` : "";
        if (newSearch === location.search) return;

        const isFirstWrite = !hasWrittenUrlRef.current;
        hasWrittenUrlRef.current = true;
        syncedSearchRef.current = newSearch;
        navigate(
            {
                pathname: location.pathname,
                search: params.toString(),
                hash: location.hash,
            },
            { replace: isFirstWrite },
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
                if (fileId in store.getState().search.files) {
                    dispatch(fetchPreview({ fileId }));
                }
                break;
            }
        }
    }, [webSocketPubSubMessage]); // eslint-disable-line react-hooks/exhaustive-deps

    return (
        <div className={styles.searchWrapper}>
            {!isMobile && <ActivityBar />}
            <LeftSidebar />
            <div className={styles.mainContent}>
                <SearchResults />
            </div>
            <RightSidebar />
            {isMobile && <ActivityBar />}
        </div>
    );
};
