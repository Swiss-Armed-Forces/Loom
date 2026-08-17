import { useEffect, useState } from "react";
import { toast } from "react-toastify";

import {
    ContextCreateResponse,
    ContextSummary,
    createAiContext,
    deleteAiContext,
    listAiContexts,
} from "@app/api";

export interface UseChatbotResult {
    activeContext: ContextCreateResponse | null;
    showHistory: boolean;
    historySearch: string;
    filteredContexts: ContextSummary[];
    contextLabel: string;
    setShowHistory: (show: boolean | ((prev: boolean) => boolean)) => void;
    setHistorySearch: (text: string) => void;
    handleNewChat: () => void;
    handleSelectContext: (contextId: string) => void;
    handleDeleteContext: (contextId: string) => void;
    refreshContexts: () => void;
}

export const useChatbot = (enabled: boolean): UseChatbotResult => {
    const [contexts, setContexts] = useState<ContextSummary[]>([]);
    const [activeContext, setActiveContext] =
        useState<ContextCreateResponse | null>(null);
    const [showHistory, setShowHistory] = useState(false);
    const [historySearch, setHistorySearch] = useState("");

    useEffect(() => {
        if (!enabled) return;
        listAiContexts()
            .then(({ contexts: ctxs }) => {
                setContexts(ctxs);
                if (ctxs.length > 0) {
                    setActiveContext({ contextId: ctxs[0].contextId });
                } else {
                    return createAiContext().then((ctx) => {
                        const summary: ContextSummary = {
                            contextId: ctx.contextId,
                            createdAt: new Date(),
                            firstQuestion: undefined,
                            questionCount: 0,
                        };
                        setContexts([summary]);
                        setActiveContext(ctx);
                    });
                }
            })
            .catch(toast.error);
    }, [enabled]);

    const handleNewChat = () => {
        createAiContext()
            .then((ctx) => {
                const newSummary: ContextSummary = {
                    contextId: ctx.contextId,
                    createdAt: new Date(),
                    firstQuestion: undefined,
                    questionCount: 0,
                };
                setContexts((prev) => [newSummary, ...prev]);
                setActiveContext(ctx);
                setShowHistory(false);
            })
            .catch(toast.error);
    };

    const handleSelectContext = (contextId: string) => {
        setActiveContext({ contextId });
        setShowHistory(false);
        setHistorySearch("");
    };

    const handleDeleteContext = (contextId: string) => {
        const previous = contexts;
        const previousActive = activeContext;
        const remaining = contexts.filter((c) => c.contextId !== contextId);
        setContexts(remaining);

        if (activeContext?.contextId === contextId) {
            if (remaining.length > 0) {
                setActiveContext({ contextId: remaining[0].contextId });
            } else {
                setActiveContext(null);
            }
        }

        deleteAiContext(contextId).catch((err) => {
            console.error("Failed to delete AI context:", err);
            setContexts(previous);
            setActiveContext(previousActive);
        });
    };

    const refreshContexts = () => {
        listAiContexts()
            .then(({ contexts: ctxs }) => setContexts(ctxs))
            .catch(() => {});
    };

    useEffect(() => {
        if (showHistory && enabled) {
            listAiContexts()
                .then(({ contexts: ctxs }) => setContexts(ctxs))
                .catch(() => {});
        }
    }, [showHistory, enabled]);

    const activeContextSummary = contexts.find(
        (c) => c.contextId === activeContext?.contextId,
    );
    const contextLabel = activeContextSummary?.firstQuestion
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

    return {
        activeContext,
        showHistory,
        historySearch,
        filteredContexts,
        contextLabel,
        setShowHistory,
        setHistorySearch,
        handleNewChat,
        handleSelectContext,
        handleDeleteContext,
        refreshContexts,
    };
};
