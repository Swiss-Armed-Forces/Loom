import { Box, Chip, Divider, Tooltip, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { ChatWindow } from "./ChatWindow";
import type { ChatMessage } from "./ChatWindow.types";
import { MessageInput } from "./MessageInput";
import { useChatbotAgent } from "./useChatbotAgent";

interface ChatbotInnerProps {
    contextId: string;
    onCitationClick: (fileId: string) => void;
    onRunComplete: () => void;
}

export const ChatbotInner = ({
    contextId,
    onCitationClick,
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
        pendingCapabilityRequest,
        activeCapabilities,
        turnActivity,
        handleSendMessage,
        handleQuestionAnswer,
        handleCapabilityAnswer,
        toggleCapability,
        abortRun,
    } = useChatbotAgent(contextId, onRunComplete);

    const messagesWithActivity: ChatMessage[] = [
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
    ];

    return (
        <>
            <Box sx={{ flexGrow: 1, overflowY: "auto", p: 1 }}>
                <ChatWindow
                    messages={messagesWithActivity}
                    isLoading={isLoading}
                    query={null}
                    onSuggestedQuestion={handleSendMessage}
                    onCitationClick={onCitationClick}
                    isInterrupted={isInterrupted}
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
            {pendingCapabilityRequest && (
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
                        Enable Research Mode?
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                        {pendingCapabilityRequest.reason}
                    </Typography>
                    <Box sx={{ display: "flex", gap: 1 }}>
                        <Chip
                            label="Allow"
                            size="small"
                            color="primary"
                            clickable
                            onClick={() => handleCapabilityAnswer(true)}
                        />
                        <Chip
                            label="Deny"
                            size="small"
                            clickable
                            onClick={() => handleCapabilityAnswer(false)}
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
                    Capabilities
                </Typography>
                <Tooltip title={t("chatbot.deepSearchTooltip")}>
                    <Chip
                        data-tour="chat-deep-search"
                        label="Research Mode"
                        size="small"
                        color="primary"
                        variant={
                            activeCapabilities.has("research_mode")
                                ? "filled"
                                : "outlined"
                        }
                        clickable
                        onClick={() => toggleCapability("research_mode")}
                    />
                </Tooltip>
            </Box>
            <Divider />
            <Box sx={{ p: 1.5 }} data-tour="chat-input">
                <MessageInput
                    disabled={
                        isLoading ||
                        pendingQuestion !== null ||
                        pendingCapabilityRequest !== null
                    }
                    onSendMessage={handleSendMessage}
                    onStop={abortRun}
                />
            </Box>
        </>
    );
};
