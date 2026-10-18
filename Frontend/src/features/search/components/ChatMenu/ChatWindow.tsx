import { KeyboardArrowDown } from "@mui/icons-material";
import { Box, Button, Fab, List, ListItem, Typography } from "@mui/material";
import { alpha } from "@mui/material/styles";
import type { Theme } from "@mui/material/styles";
import { useRef, useEffect, useState, useCallback } from "react";

import { AssistantAvatar } from "./AssistantAvatar";
import type { ChatWindowProps } from "./ChatWindow.types";
import { MAX_VISIBLE_MESSAGES } from "./ChatWindow.types";
import { EmptyState } from "./EmptyState";
import { LiveTurn } from "./LiveTurn";
import { MessageList } from "./MessageList";
import { PendingQuestion } from "./PendingQuestion";
import { TypingIndicator } from "./TypingIndicator";

// Module constants rather than literals in the render body, so emotion is not
// asked to re-serialise them on every streamed token.
const LOAD_EARLIER_SX = {
    display: "flex",
    justifyContent: "center",
    pt: 1,
} as const;

const ROW_SX = { px: 0.5, py: 0.5 } as const;
const ASSISTANT_ROW_SX = {
    ...ROW_SX,
    justifyContent: "flex-start",
    alignItems: "flex-end",
} as const;

const TYPING_BUBBLE_SX = (theme: Theme) => ({
    backgroundColor: alpha(theme.palette.text.primary, 0.06),
    borderRadius: "18px 18px 18px 4px",
    px: 1.5,
    py: 0.5,
});

const INTERRUPTED_SX = (theme: Theme) => ({
    px: 1.5,
    py: 0.75,
    borderRadius: 2,
    bgcolor: alpha(theme.palette.warning.main, 0.08),
    border: "1px solid",
    borderColor: alpha(theme.palette.warning.main, 0.3),
});

const SCROLL_FAB_SX = {
    position: "sticky",
    bottom: 8,
    left: "50%",
    transform: "translateX(-50%)",
    zIndex: 1,
    opacity: 0.85,
    width: 32,
    height: 32,
    minHeight: 32,
} as const;

export const ChatWindow = ({
    messages,
    isLoading,
    query,
    onSuggestedQuestion,
    isInterrupted,
    pendingQuestion,
    onQuestionAnswer,
    scrollContainerRef,
    turnActivity,
    isTurnActive,
    reasoningText,
    reasoningPhase,
}: ChatWindowProps) => {
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [showAll, setShowAll] = useState(false);
    const [showScrollButton, setShowScrollButton] = useState(false);
    const handleShowAll = useCallback(() => setShowAll(true), []);
    const prevLengthRef = useRef(messages.length);

    const hiddenCount = messages.length - MAX_VISIBLE_MESSAGES;
    const visibleMessages =
        !showAll && hiddenCount > 0
            ? messages.slice(-MAX_VISIBLE_MESSAGES)
            : messages;

    useEffect(() => {
        const prevLength = prevLengthRef.current;
        prevLengthRef.current = messages.length;

        if (messages.length > prevLength) {
            messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages.length]);

    const checkAtBottom = useCallback(() => {
        const el = scrollContainerRef?.current;
        if (!el) return true;
        return el.scrollHeight - el.scrollTop - el.clientHeight < 30;
    }, [scrollContainerRef]);

    useEffect(() => {
        const el = scrollContainerRef?.current;
        if (!el) return;
        const onScroll = () => setShowScrollButton(!checkAtBottom());
        el.addEventListener("scroll", onScroll, { passive: true });
        return () => el.removeEventListener("scroll", onScroll);
    }, [scrollContainerRef, checkAtBottom]);

    // Deliberately keyed on the message count rather than the array: reading
    // scrollHeight forces a synchronous reflow, and depending on `messages`
    // would do that once per streamed token. The scroll listener above keeps
    // the flag honest in between.
    useEffect(() => {
        setShowScrollButton(!checkAtBottom());
    }, [
        messages.length,
        isLoading,
        pendingQuestion,
        isInterrupted,
        checkAtBottom,
    ]);

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, []);

    if (messages.length === 0 && !isLoading && !isTurnActive) {
        return (
            <EmptyState
                query={query}
                onSuggestedQuestion={onSuggestedQuestion}
            />
        );
    }

    return (
        <>
            {!showAll && hiddenCount > 0 && (
                <Box sx={LOAD_EARLIER_SX}>
                    <Button size="small" variant="text" onClick={handleShowAll}>
                        Load {hiddenCount} earlier message
                        {hiddenCount !== 1 ? "s" : ""}
                    </Button>
                </Box>
            )}
            <List disablePadding>
                <MessageList messages={visibleMessages} />
                {isTurnActive && (
                    <ListItem sx={ASSISTANT_ROW_SX}>
                        <LiveTurn
                            activity={turnActivity}
                            reasoningText={reasoningText}
                            isThinking={reasoningPhase === "thinking"}
                        />
                    </ListItem>
                )}
                {pendingQuestion && (
                    <ListItem sx={ROW_SX}>
                        <PendingQuestion
                            question={pendingQuestion.question}
                            options={pendingQuestion.options}
                            onAnswer={(answer) => onQuestionAnswer?.(answer)}
                        />
                    </ListItem>
                )}
                {isLoading && (
                    <ListItem sx={ASSISTANT_ROW_SX}>
                        <AssistantAvatar />
                        <Box sx={TYPING_BUBBLE_SX}>
                            <TypingIndicator />
                        </Box>
                    </ListItem>
                )}
                {isInterrupted && (
                    <ListItem sx={ROW_SX}>
                        <Box sx={INTERRUPTED_SX}>
                            <Typography variant="caption" color="warning.main">
                                Agent paused — waiting for confirmation
                            </Typography>
                        </Box>
                    </ListItem>
                )}
            </List>
            <div ref={messagesEndRef} />
            {showScrollButton && (
                <Fab size="small" onClick={scrollToBottom} sx={SCROLL_FAB_SX}>
                    {isLoading ? (
                        <TypingIndicator color="primary" />
                    ) : (
                        <KeyboardArrowDown fontSize="small" />
                    )}
                </Fab>
            )}
        </>
    );
};
