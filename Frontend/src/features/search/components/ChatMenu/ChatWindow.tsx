import { KeyboardArrowDown } from "@mui/icons-material";
import { Box, Button, Fab, List, ListItem, Typography } from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";
import { useRef, useEffect, useState, useCallback } from "react";

import { AssistantAvatar } from "./AssistantAvatar";
import type { ChatWindowProps } from "./ChatWindow.types";
import { MAX_VISIBLE_MESSAGES } from "./ChatWindow.types";
import { EmptyState } from "./EmptyState";
import { MessageBubble } from "./MessageBubble";
import { PendingQuestion } from "./PendingQuestion";
import { TypingIndicator } from "./TypingIndicator";

export const ChatWindow = ({
    messages,
    isLoading,
    query,
    onSuggestedQuestion,
    isInterrupted,
    pendingQuestion,
    onQuestionAnswer,
    scrollContainerRef,
}: ChatWindowProps) => {
    const theme = useTheme();
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

    useEffect(() => {
        setShowScrollButton(!checkAtBottom());
    }, [messages, isLoading, pendingQuestion, isInterrupted, checkAtBottom]);

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, []);

    if (messages.length === 0 && !isLoading) {
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
                <Box sx={{ display: "flex", justifyContent: "center", pt: 1 }}>
                    <Button size="small" variant="text" onClick={handleShowAll}>
                        Load {hiddenCount} earlier message
                        {hiddenCount !== 1 ? "s" : ""}
                    </Button>
                </Box>
            )}
            <List disablePadding>
                {visibleMessages.map((message, index) => (
                    <ListItem
                        key={message.id ?? index}
                        sx={{
                            justifyContent: message.isUser
                                ? "flex-end"
                                : "flex-start",
                            alignItems: "flex-end",
                            px: 0.5,
                            py: 0.5,
                        }}
                    >
                        <MessageBubble message={message} />
                    </ListItem>
                ))}
                {pendingQuestion && (
                    <ListItem sx={{ px: 0.5, py: 0.5 }}>
                        <PendingQuestion
                            question={pendingQuestion.question}
                            options={pendingQuestion.options}
                            onAnswer={(answer) => onQuestionAnswer?.(answer)}
                        />
                    </ListItem>
                )}
                {isLoading && (
                    <ListItem
                        sx={{
                            justifyContent: "flex-start",
                            alignItems: "flex-end",
                            px: 0.5,
                            py: 0.5,
                        }}
                    >
                        <AssistantAvatar />
                        <Box
                            sx={{
                                backgroundColor: alpha(
                                    theme.palette.text.primary,
                                    0.06,
                                ),
                                borderRadius: "18px 18px 18px 4px",
                                px: 1.5,
                                py: 0.5,
                            }}
                        >
                            <TypingIndicator />
                        </Box>
                    </ListItem>
                )}
                {isInterrupted && (
                    <ListItem sx={{ px: 0.5, py: 0.5 }}>
                        <Box
                            sx={{
                                px: 1.5,
                                py: 0.75,
                                borderRadius: 2,
                                bgcolor: alpha(
                                    theme.palette.warning.main,
                                    0.08,
                                ),
                                border: "1px solid",
                                borderColor: alpha(
                                    theme.palette.warning.main,
                                    0.3,
                                ),
                            }}
                        >
                            <Typography variant="caption" color="warning.main">
                                Agent paused — waiting for confirmation
                            </Typography>
                        </Box>
                    </ListItem>
                )}
            </List>
            <div ref={messagesEndRef} />
            {showScrollButton && (
                <Fab
                    size="small"
                    onClick={scrollToBottom}
                    sx={{
                        position: "sticky",
                        bottom: 8,
                        left: "50%",
                        transform: "translateX(-50%)",
                        zIndex: 1,
                        opacity: 0.85,
                        width: 32,
                        height: 32,
                        minHeight: 32,
                    }}
                >
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
