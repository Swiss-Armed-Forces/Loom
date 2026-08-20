import { Box, Button, List, ListItem, Typography } from "@mui/material";
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
}: ChatWindowProps) => {
    const theme = useTheme();
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [showAll, setShowAll] = useState(false);
    const handleShowAll = useCallback(() => setShowAll(true), []);

    const hiddenCount = messages.length - MAX_VISIBLE_MESSAGES;
    const visibleMessages =
        !showAll && hiddenCount > 0
            ? messages.slice(-MAX_VISIBLE_MESSAGES)
            : messages;

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isLoading, pendingQuestion]);

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
        </>
    );
};
