import { Box, Chip, Divider, Tooltip, Typography } from "@mui/material";
import { useMemo, useRef } from "react";
import { useTranslation } from "react-i18next";

import { ChatWindow } from "./ChatWindow";
import type { ChatMessage } from "./ChatWindow.types";
import { MessageInput } from "./MessageInput";
import { useChatbotAgent } from "./useChatbotAgent";

interface ChatbotInnerProps {
    contextId: string;
    onRunComplete: () => void;
}

export const ChatbotInner = ({
    contextId,
    onRunComplete,
}: ChatbotInnerProps) => {
    const { t } = useTranslation();
    const {
        chatMessages,
        isLoading,
        isInterrupted,
        inFlightToolCalls,
        reasoningPhase,
        reasoningText,
        pendingQuestion,
        pendingModeRequest,
        activeMode,
        turnActivity,
        handleSendMessage,
        handleQuestionAnswer,
        handleModeAnswer,
        toggleMode,
        abortRun,
    } = useChatbotAgent(contextId, onRunComplete);

    const messagesWithActivity = useMemo<ChatMessage[]>(
        () => [
            ...chatMessages,
            ...((Object.keys(inFlightToolCalls).length > 0 ||
            reasoningPhase !== "idle"
                ? [
                      {
                          id: "__inflight__",
                          text: "",
                          isUser: false as const,
                          citations: [],
                          activity: [
                              ...turnActivity,
                              ...(reasoningPhase === "thinking"
                                  ? [
                                        {
                                            type: "reasoning" as const,
                                            text: reasoningText,
                                        },
                                    ]
                                  : []),
                          ],
                      },
                  ]
                : []) satisfies ChatMessage[]),
        ],
        [
            chatMessages,
            inFlightToolCalls,
            reasoningPhase,
            reasoningText,
            turnActivity,
        ],
    );

    const scrollContainerRef = useRef<HTMLDivElement>(null);

    return (
        <>
            <Box
                ref={scrollContainerRef}
                sx={{ flexGrow: 1, overflowY: "auto", p: 1 }}
                data-tour="chat-messages"
            >
                <ChatWindow
                    messages={messagesWithActivity}
                    isLoading={isLoading}
                    query={null}
                    onSuggestedQuestion={handleSendMessage}
                    isInterrupted={isInterrupted}
                    scrollContainerRef={scrollContainerRef}
                    pendingQuestion={
                        pendingQuestion
                            ? {
                                  question: pendingQuestion.question,
                                  options: pendingQuestion.options,
                              }
                            : null
                    }
                    onQuestionAnswer={handleQuestionAnswer}
                />
            </Box>
            {pendingModeRequest && (
                <Box
                    sx={{
                        px: 1.5,
                        py: 1,
                        borderTop: 1,
                        borderColor: "divider",
                        bgcolor: "action.hover",
                    }}
                >
                    <Typography variant="caption" color="text.secondary">
                        Switch to {pendingModeRequest.mode} mode?
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                        {pendingModeRequest.reason}
                    </Typography>
                    <Box sx={{ display: "flex", gap: 1 }}>
                        <Chip
                            label="Allow"
                            size="small"
                            color="primary"
                            clickable
                            onClick={() => handleModeAnswer(true)}
                        />
                        <Chip
                            label="Deny"
                            size="small"
                            clickable
                            onClick={() => handleModeAnswer(false)}
                        />
                    </Box>
                </Box>
            )}
            <Divider />
            <Box
                sx={{
                    px: 1.5,
                    py: 0.5,
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                }}
            >
                <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ whiteSpace: "nowrap" }}
                >
                    Mode
                </Typography>
                <Tooltip title={t("chatbot.modeTooltip_chat")} placement="top">
                    <Chip
                        label="Chat"
                        size="small"
                        color="primary"
                        variant={activeMode === "chat" ? "filled" : "outlined"}
                        clickable
                        onClick={() => toggleMode("chat")}
                    />
                </Tooltip>
                <Tooltip title={t("chatbot.modeTooltip_work")} placement="top">
                    <Chip
                        label="Work"
                        size="small"
                        color="primary"
                        variant={activeMode === "work" ? "filled" : "outlined"}
                        clickable
                        onClick={() => toggleMode("work")}
                    />
                </Tooltip>
                <Tooltip
                    title={t("chatbot.modeTooltip_research")}
                    placement="top"
                >
                    <Chip
                        data-tour="chat-deep-search"
                        label="Research"
                        size="small"
                        color="primary"
                        variant={
                            activeMode === "research" ? "filled" : "outlined"
                        }
                        clickable
                        onClick={() => toggleMode("research")}
                    />
                </Tooltip>
            </Box>
            <Divider />
            <Box sx={{ p: 1.5 }} data-tour="chat-input">
                <MessageInput
                    disabled={
                        isLoading ||
                        pendingQuestion !== null ||
                        pendingModeRequest !== null
                    }
                    onSendMessage={handleSendMessage}
                    onStop={abortRun}
                />
            </Box>
        </>
    );
};
