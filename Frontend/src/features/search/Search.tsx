import { t } from "i18next";
import {
    BaseSyntheticEvent,
    useEffect,
    useRef,
    useState,
    useCallback,
} from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "react-toastify";

import {
    loadLanguages,
    loadTags,
    MessageFileUpdate,
    loadSummarizationSystemPrompt,
    MessageQueryIdExpired,
    MessageError,
} from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    openDialog,
    selectDialogs,
    startLoadingIndicator,
    stopLoadingIndicator,
} from "@app/slices/commonSlice";
import {
    fetchPreview,
    selectWebSocketPubSubMessage,
    setChatbotOpen,
    setLanguages,
    updateQuery,
    setSummarizationSystemPrompt,
    setTags,
    selectQuery,
    selectLanguages,
} from "@app/slices/searchSlice";
import { DialogType } from "@features/common/utils/enums";
import { FileDetailTab } from "@features/common/utils/enums";
import {
    ChatMenu,
    ScrollToTop,
    SideMenu,
    Toolbar,
} from "@features/search/components";
import { useKeyboardNavigation } from "@features/search/hooks/useKeyboardNavigation";
import { SearchResults } from "@features/search/views/SearchResults";

import { websocketConnect } from "../../middleware/SocketMiddleware";
import { isSortDirection, SearchQuery } from "../common/utils/model";

import styles from "./Search.module.css";

const RELOAD_TIMEOUT_MS = 5_000;
const UPDATE_QUERY_DEBOUNCE_MS = 2_000;

export const Search = () => {
    const dispatch = useAppDispatch();
    const languages = useAppSelector(selectLanguages);
    const searchQuery = useAppSelector(selectQuery);
    const webSocketPubSubMessage = useAppSelector(selectWebSocketPubSubMessage);
    const chatbotOpen = useAppSelector((state) => state.search.chatbotOpen);
    const dialogs = useAppSelector(selectDialogs);
    const dialogFileIdRef = useRef<string>("");

    // Initialize keyboard navigation
    useKeyboardNavigation();

    const [searchParams, setSearchParams] = useSearchParams();
    const searchResultWrapper = useRef<HTMLDivElement>(null);
    const [hasScrollOffset, setHasScrollOffset] = useState(false);

    // Reset scroll position when search query changes
    useEffect(() => {
        if (searchQuery?.id) {
            searchResultWrapper.current?.scrollTo(0, 0);
        }
    }, [searchQuery?.id]);

    const updateQueryDebounceTimeoutRef = useRef<ReturnType<
        typeof setTimeout
    > | null>(null);

    const toggleChatbot = useCallback(() => {
        dispatch(setChatbotOpen(!chatbotOpen));
    }, [dispatch, chatbotOpen]);

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
                const [langs, prompt] = await Promise.all([
                    loadLanguages(),
                    loadSummarizationSystemPrompt(),
                    fetchSearchState(),
                    dispatch(websocketConnect),
                ]);
                dispatch(setLanguages(langs));
                dispatch(setSummarizationSystemPrompt(prompt));
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

        return () => clearInterval(fetchSearchStateInterval);
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    // sync URL searchParams to Redux state
    useEffect(() => {
        if (searchQuery || !languages) return;

        const query = searchParams.get("query");
        const languageCodes = searchParams.getAll("languages");
        const sortField = searchParams.get("sortField");
        const sortDirection = searchParams.get("sortDirection");

        const mappedLanguages =
            languageCodes.length > 0
                ? languageCodes.map((code) => ({
                      code,
                      name:
                          languages.find((l) => l.code === code)?.name ??
                          "missing",
                  }))
                : undefined;

        const newQuery: Partial<SearchQuery> = {
            query: query || undefined,
            languages: mappedLanguages,
            sortField: sortField || undefined,
            sortDirection: isSortDirection(sortDirection)
                ? sortDirection
                : undefined,
        };

        dispatch(updateQuery(newQuery));
    }, [languages, searchParams, searchQuery]); // eslint-disable-line react-hooks/exhaustive-deps

    // load file detail
    useEffect(() => {
        const handleHashChange = () => {
            const fileId = window.location.hash.substring(1);

            // Clear ref if hash is removed
            if (!fileId) {
                dialogFileIdRef.current = undefined;
                return;
            }

            // Check if dialog is already open for this fileId
            const isDialogAlreadyOpen =
                dialogFileIdRef.current === fileId ||
                dialogs.some(
                    (d) =>
                        d.type === DialogType.FileDetail &&
                        d.props.fileId === fileId,
                );

            if (isDialogAlreadyOpen) {
                return;
            }

            // Open new dialog
            dispatch(
                openDialog({
                    id: "",
                    type: DialogType.FileDetail,
                    props: { fileId, tab: FileDetailTab.Rendered },
                }),
            );
            dialogFileIdRef.current = fileId;
        };

        // Run on mount and when hash changes
        handleHashChange();

        window.addEventListener("hashchange", handleHashChange);

        return () => {
            window.removeEventListener("hashchange", handleHashChange);
        };
    }, [dialogs]); // eslint-disable-line react-hooks/exhaustive-deps

    // persist in query params
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

        searchQuery.languages?.forEach((l) => {
            params.append("languages", l.code);
        });

        // Sync with Router
        // We use { replace: true } to avoid polluting the history stack
        const currentHash = window.location.hash;
        setSearchParams(params, { replace: true });

        if (currentHash) {
            window.history.replaceState(
                null,
                "",
                `${window.location.pathname}?${params.toString()}${currentHash}`,
            );
        }
    }, [searchQuery, setSearchParams]);

    useEffect(() => {
        if (!webSocketPubSubMessage) return;
        const { message } = webSocketPubSubMessage;

        switch (message.type) {
            case "error":
                toast.error((message as MessageError).message);
                break;

            case "fileUpdate":
                // fetch file preview on change
                dispatch(
                    fetchPreview({
                        fileId: (message as MessageFileUpdate).fileId,
                    }),
                );
                break;
        }
    }, [webSocketPubSubMessage]); // eslint-disable-line react-hooks/exhaustive-deps

    // update query id and show toast
    useEffect(() => {
        const message = webSocketPubSubMessage.message as MessageQueryIdExpired;
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
            </div>
            <ChatMenu isOpen={chatbotOpen} toggleMenu={toggleChatbot} />
        </div>
    );
};
