import { BaseSyntheticEvent, useEffect, useRef, useState } from "react";
import { useAppDispatch, useAppSelector } from "../../app/hooks";
import {
    fetchPreview,
    selectWebSocketPubSubMessage,
    setChatbotOpen,
    setLanguages,
    updateQuery,
    setSummarizationSystemPrompt,
    setTags,
    selectFileDetailData,
    setFileDetailData,
} from "./searchSlice";
import {
    loadLanguages,
    LibretranslateSupportedLanguages,
    loadTags,
    MessageFileUpdate,
    loadSummarizationSystemPrompt,
    MessageQueryIdExpired,
} from "../../app/api";
import {
    handleError,
    startLoadingIndicator,
    stopLoadingIndicator,
} from "../common/commonSlice";
import { SearchResults } from "./container/SearchResults";
import { SideMenu } from "./components/SideMenu";
import styles from "./Search.module.css";
import { FileDetailDialog } from "./components/FileDetailDialog.tsx";
import { Toolbar } from "./components/Toolbar.tsx";
import { ScrollToTop } from "./components/ScrollToTop.tsx";
import { selectQuery, selectLanguages } from "./searchSlice";
import { isSortDirection, SearchQuery } from "./model";
import { websocketConnect } from "../../middleware/SocketMiddleware.ts";
import { toast } from "react-toastify";
import { MessageError } from "../../app/api";
import ChatMenu from "./components/ChatMenu.tsx";
import { useSearchParams } from "react-router-dom";
import { t } from "i18next";

const RELOAD_TIMEOUT__MS = 5_000;
const FILE_FETCH_DEBOUNCE__MS = 2_000;
const UPDATE_QUERY_DEBOUNCE__MS = 2_000;

export function Search() {
    const dispatch = useAppDispatch();
    const languages = useAppSelector(selectLanguages);
    const searchQuery = useAppSelector(selectQuery);
    const fileDetailDialogData = useAppSelector(selectFileDetailData);
    const webSocketPubSubMessage = useAppSelector(selectWebSocketPubSubMessage);

    const chatbotOpen = useAppSelector((state) => state.search.chatbotOpen);

    const [searchParams, setSearchParams] = useSearchParams();
    const searchResultWrapper = useRef<HTMLDivElement>(null);
    const [hasScrollOffset, setHasScrollOffset] = useState(false);

    const fileFetchDebounceTimeouts = new Map<
        string,
        ReturnType<typeof setTimeout> // see: https://stackoverflow.com/a/56239226/3215929
    >();

    const updateQueryDebounceTimeouts = new Map<
        string,
        ReturnType<typeof setTimeout> // see: https://stackoverflow.com/a/56239226/3215929
    >();

    const toggleChatbot = () => {
        dispatch(setChatbotOpen(!chatbotOpen));
    };

    useEffect(() => {
        async function fetchInitialSearchState() {
            await Promise.all([
                fetchSearchState(),
                dispatch(websocketConnect),
                dispatch(setLanguages(await loadLanguages())),
                dispatch(
                    setSummarizationSystemPrompt(
                        await loadSummarizationSystemPrompt(),
                    ),
                ),
            ]).catch((errorPayload) => {
                dispatch(handleError(errorPayload));
            });
        }
        async function fetchSearchState() {
            await Promise.all([dispatch(setTags(await loadTags()))]).catch(
                (errorPayload) => {
                    dispatch(handleError(errorPayload));
                },
            );
        }

        async function load() {
            dispatch(startLoadingIndicator());
            try {
                await fetchInitialSearchState();
            } finally {
                dispatch(stopLoadingIndicator());
            }

            // refresh search state after timeout
            setInterval(fetchSearchState, RELOAD_TIMEOUT__MS);
        }
        load();
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        if (searchQuery) return;
        if (!languages) return;
        const query = searchParams.get("query");
        const languageCodes = searchParams.getAll("languages");
        const sortField = searchParams.get("sortField");
        const sortDirection = searchParams.get("sortDirection");
        const newQuery = {
            ...(query && {
                query: query,
            }),
            ...(languageCodes.length > 0 && {
                languages: languageCodes.map(
                    (c) =>
                        ({
                            code: c,
                            name:
                                languages?.find((l) => l.code === c)?.name ??
                                "missing",
                        }) as LibretranslateSupportedLanguages,
                ),
            }),
            ...(sortField && {
                sortField: sortField,
            }),
            ...(sortDirection &&
                isSortDirection(sortDirection) && {
                    sortDirection: sortDirection,
                }),
        } as SearchQuery;
        dispatch(updateQuery(newQuery));
        // load fileId
        const fileId = window.location.hash.substring(1); // substring: remove '#'
        if (!fileId) return;
        dispatch(setFileDetailData({ fileId: fileId }));
    }, [languages]); // eslint-disable-line react-hooks/exhaustive-deps

    // persist in query params
    useEffect(() => {
        if (!searchQuery) return;

        const newSearchParams = new URLSearchParams({
            ...(searchQuery.query && { query: searchQuery.query }),
            ...(searchQuery.sortField && {
                sortField: searchQuery.sortField,
            }),
            ...(searchQuery.sortDirection && {
                sortDirection: searchQuery.sortDirection,
            }),
        });
        // Map to multiple language params, join with `newSearchParams()`
        if (searchQuery.languages) {
            searchQuery.languages.map((l) =>
                newSearchParams.append("languages", l.code),
            );
        }

        // Update URL with new search params
        setSearchParams(newSearchParams);

        // If there was an selected file id previously, add it back to the URL
        if (!fileDetailDialogData) return;
        window.history.replaceState(
            null,
            "",
            `${window.location.pathname}?${newSearchParams.toString()}#${fileDetailDialogData.fileId}`,
        );
    }, [searchQuery, fileDetailDialogData, setSearchParams, location.hash]); // eslint-disable-line react-hooks/exhaustive-deps

    // print error messages as toasts
    useEffect(() => {
        if (!webSocketPubSubMessage) return;
        if (webSocketPubSubMessage.message.type !== "error") return;
        const message = webSocketPubSubMessage.message as MessageError;
        toast.error(message.message);
    }, [webSocketPubSubMessage]);

    // fetch file preview on change
    useEffect(() => {
        if (!webSocketPubSubMessage) return;
        if (webSocketPubSubMessage.message.type !== "fileUpdate") return;
        const message = webSocketPubSubMessage.message as MessageFileUpdate;

        const fileId = message.fileId;
        const existingTimeout = fileFetchDebounceTimeouts.get(fileId);
        clearTimeout(existingTimeout);
        const newTimeout = setTimeout(() => {
            dispatch(fetchPreview({ fileId: fileId }));
            fileFetchDebounceTimeouts.delete(fileId);
        }, FILE_FETCH_DEBOUNCE__MS);
        fileFetchDebounceTimeouts.set(fileId, newTimeout);
    }, [webSocketPubSubMessage]); // eslint-disable-line react-hooks/exhaustive-deps

    // update query id and show toast
    useEffect(() => {
        if (!webSocketPubSubMessage) return;
        if (webSocketPubSubMessage.message.type !== "queryIdExpired") return;
        const message = webSocketPubSubMessage.message as MessageQueryIdExpired;
        if (searchQuery?.id !== message.oldId) return;

        const oldQueryId = message.oldId;
        const existingTimeout = updateQueryDebounceTimeouts.get(oldQueryId);
        clearTimeout(existingTimeout);
        const newTimeout = setTimeout(() => {
            dispatch(updateQuery({ id: message.newId }));
            toast.info(t("generalSearchView.queryExpired"));
            updateQueryDebounceTimeouts.delete(oldQueryId);
        }, UPDATE_QUERY_DEBOUNCE__MS);
        updateQueryDebounceTimeouts.set(oldQueryId, newTimeout);
    }, [webSocketPubSubMessage, searchQuery]); // eslint-disable-line react-hooks/exhaustive-deps

    const updateScrollOffset = (ev: BaseSyntheticEvent) => {
        setHasScrollOffset(ev.target.scrollTop > 0);
    };

    return (
        <div className={styles.searchWrapper}>
            <SideMenu />
            <div className={styles.mainView}>
                <Toolbar />

                <div
                    onScroll={updateScrollOffset}
                    ref={searchResultWrapper}
                    className={styles.searchResultWrapper}
                >
                    <SearchResults />
                    <ScrollToTop
                        visible={hasScrollOffset}
                        onClick={() => {
                            searchResultWrapper.current?.scrollTo(0, 0);
                        }}
                    />
                </div>

                <FileDetailDialog />
            </div>
            <ChatMenu isOpen={chatbotOpen} toggleMenu={toggleChatbot} />
        </div>
    );
}
