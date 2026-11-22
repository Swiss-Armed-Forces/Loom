import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "react-toastify";

import {
    ContextCreateResponse,
    ContextSummary,
    createAiContext,
    getContextHistory,
    listAiContexts,
    setAiContextHidden,
} from "@app/api";
import { useAppDispatch, useAppStore } from "@app/hooks";
import { setActiveContextId } from "@app/slices/searchSlice";

interface ActiveContext extends ContextCreateResponse {
    hidden?: boolean;
}

const newContextSummary = (contextId: string): ContextSummary => ({
    contextId,
    createdAt: new Date(),
    firstQuestion: undefined,
    questionCount: 0,
});

export interface UseChatbotResult {
    activeContext: ActiveContext | null;
    showHistory: boolean;
    historySearch: string;
    filteredContexts: ContextSummary[];
    contextLabel: string;
    isHidden: boolean;
    isHiddenPending: boolean;
    setShowHistory: (show: boolean | ((prev: boolean) => boolean)) => void;
    setHistorySearch: (text: string) => void;
    handleToggleHistory: () => void;
    handleNewChat: () => void;
    handleHideActiveContext: () => void;
    handleUnhideActiveContext: () => void;
    handleSelectContext: (contextId: string) => void;
    handleHideContext: (contextId: string) => void;
    refreshContexts: () => void;
}

export const useChatbot = (enabled: boolean): UseChatbotResult => {
    const dispatch = useAppDispatch();
    const store = useAppStore();
    const [contexts, setContexts] = useState<ContextSummary[]>([]);
    const [activeContext, setActiveContext] = useState<ActiveContext | null>(
        null,
    );
    const [showHistory, setShowHistory] = useState(false);
    const [historySearch, setHistorySearch] = useState("");
    const [isHiddenPending, setIsHiddenPending] = useState(false);

    // The active chat as it stands now, for the handlers that decide on it
    // after an await.
    const activeContextRef = useRef(activeContext);

    useEffect(() => {
        activeContextRef.current = activeContext;
        if (activeContext?.contextId) {
            dispatch(setActiveContextId(activeContext.contextId));
        }
    }, [activeContext, dispatch]);

    const isHidden = activeContext?.hidden ?? false;

    const refreshContexts = useCallback(() => {
        listAiContexts()
            .then(({ contexts: ctxs }) => setContexts(ctxs))
            .catch(() => {});
    }, []);

    // Opening the chat panel restores the chat the user last selected. The
    // panel mounts once and stays mounted, so this runs again on every switch
    // back to it — a chat already open is the one to keep.
    useEffect(() => {
        if (!enabled || activeContext) return;
        let cancelled = false;

        const openNewest = (ctxs: ContextSummary[]) => {
            if (ctxs.length > 0) {
                setActiveContext({ contextId: ctxs[0].contextId });
                return;
            }
            return createAiContext().then((ctx) => {
                if (cancelled) return;
                setContexts([newContextSummary(ctx.contextId)]);
                setActiveContext(ctx);
            });
        };

        listAiContexts()
            .then(({ contexts: ctxs }) => {
                if (cancelled) return;
                setContexts(ctxs);

                const lastId = store.getState().search.activeContextId;
                if (!lastId) return openNewest(ctxs);

                if (ctxs.some((c) => c.contextId === lastId)) {
                    setActiveContext({ contextId: lastId });
                    return;
                }

                // A context the list does not carry is either hidden, since
                // the list excludes those, or gone. Its history tells the two
                // apart and is the only way back to a hidden chat, whose
                // messages useChatbotAgent then reads from the backend.
                return getContextHistory(lastId, { pageSize: 1 })
                    .then(({ hidden }) => {
                        if (cancelled) return;
                        setActiveContext({ contextId: lastId, hidden });
                    })
                    .catch(() => {
                        if (cancelled) return;
                        return openNewest(ctxs);
                    });
            })
            .catch(toast.error);

        return () => {
            cancelled = true;
        };
    }, [enabled, activeContext, store]);

    const handleNewChat = () => {
        createAiContext()
            .then((ctx) => {
                setContexts((prev) => [
                    newContextSummary(ctx.contextId),
                    ...prev,
                ]);
                setActiveContext(ctx);
                setShowHistory(false);
            })
            .catch(toast.error);
    };

    /**
     * Puts the active chat in or out of the conversation list. The list cannot
     * carry a hidden context, so hiding drops its row and unhiding fetches the
     * list again.
     */
    const setActiveHidden = async (hidden: boolean) => {
        const contextId = activeContext?.contextId;
        if (!contextId) return;

        setIsHiddenPending(true);
        try {
            await setAiContextHidden(contextId, hidden);

            if (hidden) {
                setContexts((ctxs) =>
                    ctxs.filter((c) => c.contextId !== contextId),
                );
            } else {
                refreshContexts();
            }

            setActiveContext({ contextId, hidden });
        } catch (error) {
            toast.error(
                hidden
                    ? "Failed to hide this conversation"
                    : "Failed to show this conversation",
            );
            console.error(error);
        } finally {
            setIsHiddenPending(false);
        }
    };

    const handleHideActiveContext = () => setActiveHidden(true);

    const handleUnhideActiveContext = () => setActiveHidden(false);

    const handleSelectContext = (contextId: string) => {
        setActiveContext({ contextId });
        setShowHistory(false);
        setHistorySearch("");
    };

    useEffect(() => {
        if (showHistory && enabled) refreshContexts();
    }, [showHistory, enabled, refreshContexts]);

    // The list only carries visible contexts, so a row can only be hidden
    // from here. Hiding the active chat leaves nothing open, so a fresh one
    // takes its place.
    const handleHideContext = async (contextId: string) => {
        try {
            await setAiContextHidden(contextId, true);
        } catch (error) {
            toast.error("Failed to hide this conversation");
            console.error(error);
            return;
        }

        setContexts((ctxs) => ctxs.filter((c) => c.contextId !== contextId));

        // The chat may have been switched while the request was in flight,
        // which the ref sees and the render closure does not.
        if (activeContextRef.current?.contextId !== contextId) return;

        try {
            const ctx = await createAiContext();
            setContexts((prev) => [newContextSummary(ctx.contextId), ...prev]);
            setActiveContext(ctx);
            setShowHistory(false);
        } catch (error) {
            toast.error("Failed to open a new conversation");
            console.error(error);
        }
    };

    const activeContextSummary = contexts.find(
        (c) => c.contextId === activeContext?.contextId,
    );
    const contextLabel = isHidden
        ? "Hidden chat"
        : activeContextSummary?.firstQuestion
          ? activeContextSummary.firstQuestion.slice(0, 40)
          : activeContext
            ? `New chat — ${new Date().toLocaleDateString()}`
            : "Loading…";

    const filteredContexts = historySearch
        ? contexts.filter((c) =>
              c.firstQuestion
                  ?.toLowerCase()
                  .includes(historySearch.toLowerCase()),
          )
        : contexts;

    const handleToggleHistory = () => {
        setShowHistory((prev) => !prev);
    };

    return {
        activeContext,
        showHistory,
        historySearch,
        filteredContexts,
        contextLabel,
        isHidden,
        isHiddenPending,
        setShowHistory,
        setHistorySearch,
        handleToggleHistory,
        handleNewChat,
        handleHideActiveContext,
        handleUnhideActiveContext,
        handleSelectContext,
        handleHideContext,
        refreshContexts,
    };
};
