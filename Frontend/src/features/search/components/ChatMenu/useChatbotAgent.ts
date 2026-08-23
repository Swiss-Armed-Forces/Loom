import { HttpAgent } from "@ag-ui/client";
import type { AgentSubscriber, Tool } from "@ag-ui/client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { getContextHistory, setAiContextMode } from "@app/api";
import { apiConfiguration } from "@app/api/apiConfiguration";
import { store } from "@app/store";

import {
    createErrorMessage,
    getToolLabel,
    mapToChatMessages,
} from "./chatbotUtils";
import type {
    ActivityRecord,
    ChatCitation,
    ChatMessage,
    ToolCallRecord,
} from "./ChatWindow.types";
import { createFrontendTools } from "./tools";

export interface UseChatbotAgentResult {
    chatMessages: ChatMessage[];
    isLoading: boolean;
    isInterrupted: boolean;
    inFlightToolCalls: Record<string, ToolCallRecord>;
    reasoningPhase: "idle" | "thinking" | "done";
    reasoningText: string;
    pendingQuestion: {
        toolCallId: string;
        question: string;
        options: string[];
    } | null;
    pendingModeRequest: {
        toolCallId: string;
        mode: string;
        reason: string;
    } | null;
    activeMode: string;
    turnActivity: ActivityRecord[];
    handleSendMessage: (text: string) => Promise<void>;
    handleQuestionAnswer: (answer: string) => void;
    handleModeAnswer: (allow: boolean) => Promise<void>;
    toggleMode: (mode: string) => void;
    abortRun: () => void;
    contextId: string;
}

export const useChatbotAgent = (
    contextId: string,
    onRunComplete: () => void,
): UseChatbotAgentResult => {
    const { t } = useTranslation();
    const onRunCompleteRef = useRef(onRunComplete);
    onRunCompleteRef.current = onRunComplete;

    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [inFlightToolCalls, setInFlightToolCalls] = useState<
        Record<string, ToolCallRecord>
    >({});
    const [reasoningText, setReasoningText] = useState("");
    const [reasoningPhase, setReasoningPhase] = useState<
        "idle" | "thinking" | "done"
    >("idle");
    const reasoningTextRef = useRef("");
    const [isInterrupted, setIsInterrupted] = useState(false);
    const [pendingQuestion, setPendingQuestion] = useState<{
        toolCallId: string;
        question: string;
        options: string[];
    } | null>(null);
    const [activeMode, setActiveMode] = useState<string>("work");
    const activeModeRef = useRef<string>("work");
    const [pendingModeRequest, setPendingModeRequest] = useState<{
        toolCallId: string;
        mode: string;
        reason: string;
    } | null>(null);
    const agentRef = useRef<HttpAgent | null>(null);
    const citationsRef = useRef<Record<string, ChatCitation[]>>({});
    const runToolCallsRef = useRef<Record<string, ToolCallRecord>>({});
    const streamingMsgIdRef = useRef<string | null>(null);
    const activityRef = useRef<Record<string, ActivityRecord[]>>({});
    const turnActivityRef = useRef<ActivityRecord[]>([]);
    const finalMsgIdsRef = useRef<Set<string>>(new Set());

    const frontendToolsRef = useRef(
        createFrontendTools(() => store.getState(), store.dispatch),
    );
    const frontendToolDefsRef = useRef<Tool[]>(
        Object.values(frontendToolsRef.current).map((t) => t.definition),
    );

    const pendingFrontendToolsRef = useRef<
        {
            toolCallId: string;
            toolName: string;
            args: Record<string, unknown>;
        }[]
    >([]);
    const rerunningRef = useRef(false);
    const errorHandledRef = useRef(false);

    const getToolDefs = () => frontendToolDefsRef.current;

    const appendError = useCallback((text: string) => {
        setChatMessages((prev) => [...prev, createErrorMessage(text)]);
        setIsLoading(false);
    }, []);

    const handleRunError = useCallback(() => {
        rerunningRef.current = false;
        setInFlightToolCalls({});
        appendError("Agent error");
    }, [appendError]);

    useEffect(() => {
        const abortController = new AbortController();
        const agent = new HttpAgent({
            url: `${apiConfiguration.basePath}/v1/ai/${contextId}/run`,
        });
        agentRef.current = agent;

        getContextHistory(contextId, { pageSize: 20 }).then(
            ({ questions, activeMode: mode }) => {
                if (mode != null) {
                    activeModeRef.current = mode;
                    setActiveMode(mode);
                }
                if (!questions || questions.length === 0) return;

                for (const q of questions) {
                    const assistantMsgId = crypto.randomUUID();
                    finalMsgIdsRef.current.add(assistantMsgId);

                    const activity: ActivityRecord[] = (q.activity ?? []).map(
                        (entry) =>
                            entry.type === "reasoning"
                                ? {
                                      type: "reasoning" as const,
                                      text: entry.text ?? "",
                                  }
                                : {
                                      type: "tool_call" as const,
                                      toolCall: {
                                          id: crypto.randomUUID(),
                                          name: entry.toolName ?? "",
                                          label: getToolLabel(
                                              t,
                                              entry.toolName ?? "",
                                          ),
                                          args: JSON.stringify(
                                              entry.input ?? {},
                                          ),
                                          result: entry.output ?? "",
                                          status: "done" as const,
                                      },
                                  },
                    );
                    if (activity.length > 0) {
                        activityRef.current[assistantMsgId] = activity;
                    }

                    const citations = (q.citations ?? []).map((c) => ({
                        id: String(c.fileId),
                        fileId: String(c.fileId),
                        text: c.text,
                    }));
                    if (citations.length > 0) {
                        citationsRef.current[assistantMsgId] = citations;
                    }

                    agent.addMessage({
                        role: "user",
                        id: crypto.randomUUID(),
                        content: q.question,
                    });
                    agent.addMessage({
                        role: "assistant",
                        id: assistantMsgId,
                        content: q.answer,
                    });
                }
                setChatMessages(
                    mapToChatMessages(
                        agent.messages,
                        citationsRef.current,
                        activityRef.current,
                        finalMsgIdsRef.current,
                    ),
                );
            },
        );

        const subscriber: AgentSubscriber = {
            onRunInitialized: () => {
                setIsLoading(true);
                runToolCallsRef.current = {};
                streamingMsgIdRef.current = null;
            },
            onToolCallStartEvent: ({ event }) => {
                const label = getToolLabel(t, event.toolCallName);
                const record: ToolCallRecord = {
                    id: event.toolCallId,
                    name: event.toolCallName,
                    label,
                    args: "",
                    result: "",
                    status: "running",
                };
                runToolCallsRef.current[event.toolCallId] = record;
                turnActivityRef.current.push({
                    type: "tool_call",
                    toolCall: record,
                });
                setInFlightToolCalls((prev) => ({
                    ...prev,
                    [event.toolCallId]: record,
                }));
            },
            onToolCallArgsEvent: ({ event }) => {
                const record = runToolCallsRef.current[event.toolCallId];
                if (record) record.args += event.delta;
            },
            onToolCallResultEvent: ({ event }) => {
                const record = runToolCallsRef.current[event.toolCallId];
                if (record) record.result = event.content;
                setInFlightToolCalls((prev) => {
                    const existing = prev[event.toolCallId];
                    if (!existing) return prev;
                    return {
                        ...prev,
                        [event.toolCallId]: {
                            ...existing,
                            result: event.content,
                            status: "done",
                        },
                    };
                });
            },
            onToolCallEndEvent: ({ event, toolCallName, toolCallArgs }) => {
                if (toolCallName in frontendToolsRef.current) {
                    pendingFrontendToolsRef.current.push({
                        toolCallId: event.toolCallId,
                        toolName: toolCallName,
                        args: toolCallArgs,
                    });
                }
                const record = runToolCallsRef.current[event.toolCallId];
                if (record) record.status = "done";
                setInFlightToolCalls((prev) => {
                    const existing = prev[event.toolCallId];
                    if (!existing) return prev;
                    return {
                        ...prev,
                        [event.toolCallId]: { ...existing, status: "done" },
                    };
                });
            },
            onReasoningStartEvent: () => {
                reasoningTextRef.current = "";
                setReasoningText("");
                setReasoningPhase("thinking");
            },
            onReasoningMessageContentEvent: ({ event }) => {
                reasoningTextRef.current += event.delta;
                setReasoningText(reasoningTextRef.current);
            },
            onReasoningEndEvent: () => {
                if (reasoningTextRef.current) {
                    turnActivityRef.current.push({
                        type: "reasoning",
                        text: reasoningTextRef.current,
                    });
                }
                setReasoningPhase("done");
            },
            onRunFinishedEvent: ({ outcome, agent }) => {
                if (outcome === "interrupt") setIsInterrupted(true);

                const pending = pendingFrontendToolsRef.current;
                if (pending.length === 0) return;
                pendingFrontendToolsRef.current = [];

                const passiveItems = pending.filter((item) => {
                    const tool = frontendToolsRef.current[item.toolName];
                    return tool && !tool.interactive;
                });
                const askUserItem = pending.find(
                    (item) => item.toolName === "ask_user",
                );
                const requestModeItem = pending.find(
                    (item) => item.toolName === "request_mode",
                );

                rerunningRef.current = true;

                (async () => {
                    try {
                        for (const item of passiveItems) {
                            if (abortController.signal.aborted) {
                                rerunningRef.current = false;
                                return;
                            }
                            const tool =
                                frontendToolsRef.current[item.toolName];
                            if (!tool || tool.interactive === true) continue;
                            const result = await tool.handler(item.args);

                            if (abortController.signal.aborted) {
                                rerunningRef.current = false;
                                return;
                            }

                            const record =
                                runToolCallsRef.current[item.toolCallId];
                            if (record) {
                                record.result = result;
                                record.status = "done";
                            }
                            setInFlightToolCalls((prev) => {
                                const existing = prev[item.toolCallId];
                                if (!existing) return prev;
                                return {
                                    ...prev,
                                    [item.toolCallId]: {
                                        ...existing,
                                        result,
                                        status: "done",
                                    },
                                };
                            });

                            agent.addMessage({
                                role: "tool",
                                id: crypto.randomUUID(),
                                toolCallId: item.toolCallId,
                                content: result,
                            });
                        }

                        if (abortController.signal.aborted) {
                            rerunningRef.current = false;
                            return;
                        }

                        if (requestModeItem) {
                            const requestedMode = String(
                                requestModeItem.args.mode ?? "",
                            );
                            if (requestedMode === activeModeRef.current) {
                                agent.addMessage({
                                    role: "tool",
                                    id: crypto.randomUUID(),
                                    toolCallId: requestModeItem.toolCallId,
                                    content: "granted",
                                });
                                agent
                                    .runAgent({ tools: getToolDefs() })
                                    .catch(handleRunError);
                            } else {
                                setPendingModeRequest({
                                    toolCallId: requestModeItem.toolCallId,
                                    mode: requestedMode,
                                    reason: String(
                                        requestModeItem.args.reason ?? "",
                                    ),
                                });
                                setIsLoading(false);
                            }
                        } else if (askUserItem) {
                            setPendingQuestion({
                                toolCallId: askUserItem.toolCallId,
                                question: String(
                                    askUserItem.args.question ?? "",
                                ),
                                options: Array.isArray(askUserItem.args.options)
                                    ? (askUserItem.args.options as string[])
                                    : [],
                            });
                            setIsLoading(false);
                        } else {
                            agent
                                .runAgent({ tools: getToolDefs() })
                                .catch(handleRunError);
                        }
                    } catch {
                        rerunningRef.current = false;
                        handleRunError();
                    }
                })();
            },
            onRunErrorEvent: ({ event }) => {
                errorHandledRef.current = true;
                setInFlightToolCalls({});
                appendError(event.message ?? "Agent error");
            },
            onTextMessageStartEvent: ({ event }) => {
                streamingMsgIdRef.current = event.messageId;
                finalMsgIdsRef.current.add(event.messageId);
                setReasoningPhase("idle");
                if (turnActivityRef.current.length > 0) {
                    activityRef.current[event.messageId] = [
                        ...turnActivityRef.current,
                    ];
                }
                setInFlightToolCalls((prev) => {
                    const running: Record<string, ToolCallRecord> = {};
                    for (const [id, chip] of Object.entries(prev)) {
                        if (chip.status === "running") running[id] = chip;
                    }
                    return running;
                });
            },
            onCustomEvent: ({ event }) => {
                if (event.name !== "citation" || !streamingMsgIdRef.current) {
                    return;
                }
                const msgId = streamingMsgIdRef.current;
                const citation: ChatCitation = {
                    id: event.value.file_id,
                    fileId: event.value.file_id,
                    text: event.value.text,
                };
                citationsRef.current = {
                    ...citationsRef.current,
                    [msgId]: [...(citationsRef.current[msgId] ?? []), citation],
                };
            },
            onMessagesChanged: ({ messages }) => {
                setChatMessages(
                    mapToChatMessages(
                        messages,
                        citationsRef.current,
                        activityRef.current,
                        finalMsgIdsRef.current,
                    ),
                );
            },
            onRunFinalized: ({ messages }) => {
                if (rerunningRef.current) {
                    rerunningRef.current = false;
                } else {
                    setInFlightToolCalls({});
                    setIsLoading(false);
                    onRunCompleteRef.current();
                }
                if (!errorHandledRef.current) {
                    setChatMessages(
                        mapToChatMessages(
                            messages,
                            citationsRef.current,
                            activityRef.current,
                            finalMsgIdsRef.current,
                        ),
                    );
                }
                errorHandledRef.current = false;
            },
            onRunFailed: () => {
                errorHandledRef.current = true;
                setInFlightToolCalls({});
                appendError("Cannot get a response");
            },
        };

        const { unsubscribe } = agent.subscribe(subscriber);

        return () => {
            abortController.abort();
            unsubscribe();
            agent.abortRun();
        };
    }, [contextId, t, appendError, handleRunError]);

    const handleSendMessage = async (text: string) => {
        const agent = agentRef.current;
        if (!agent) return;

        setInFlightToolCalls({});
        reasoningTextRef.current = "";
        setReasoningText("");
        setReasoningPhase("idle");
        setIsInterrupted(false);
        turnActivityRef.current = [];
        streamingMsgIdRef.current = null;
        errorHandledRef.current = false;

        agent.addMessage({
            role: "user",
            id: crypto.randomUUID(),
            content: text,
        });
        setChatMessages(
            mapToChatMessages(
                agent.messages,
                citationsRef.current,
                activityRef.current,
                finalMsgIdsRef.current,
            ),
        );

        try {
            await agent.runAgent({ tools: getToolDefs() });
        } catch {
            appendError("Cannot get a response");
        }
    };

    const handleQuestionAnswer = (answer: string) => {
        const agent = agentRef.current;
        if (!agent || !pendingQuestion) return;
        const { toolCallId, question } = pendingQuestion;

        setInFlightToolCalls((prev) => {
            const existing = prev[toolCallId];
            if (!existing) return prev;
            return {
                ...prev,
                [toolCallId]: { ...existing, result: answer, status: "done" },
            };
        });
        const record = runToolCallsRef.current[toolCallId];
        if (record) {
            record.result = answer;
            record.status = "done";
        }

        // Tool result must immediately follow the assistant tool_call message.
        agent.addMessage({
            role: "tool",
            id: crypto.randomUUID(),
            toolCallId,
            content: answer,
        });

        // Persist the question and answer as visible chat messages.
        const questionMsgId = crypto.randomUUID();
        finalMsgIdsRef.current.add(questionMsgId);
        agent.addMessage({
            role: "assistant",
            id: questionMsgId,
            content: question,
        });
        if (answer !== "other") {
            agent.addMessage({
                role: "user",
                id: crypto.randomUUID(),
                content: answer,
            });
        }

        setPendingQuestion(null);

        if (answer === "other") {
            // Let the user type a free-form answer as their next message.
            setIsLoading(false);
            setReasoningPhase("idle");
            setInFlightToolCalls({});
        } else {
            setIsLoading(true);
            agent.runAgent({ tools: getToolDefs() }).catch(handleRunError);
        }
    };

    const handleModeAnswer = async (allow: boolean) => {
        const agent = agentRef.current;
        if (!agent || !pendingModeRequest) return;
        const { toolCallId, mode } = pendingModeRequest;

        const result = allow ? "granted" : "denied";

        if (allow) {
            try {
                await setAiContextMode(contextId, mode);
            } catch {
                appendError("Failed to update mode");
                setPendingModeRequest(null);
                rerunningRef.current = false;
                return;
            }
            activeModeRef.current = mode;
            setActiveMode(mode);
        }

        agent.addMessage({
            role: "tool",
            id: crypto.randomUUID(),
            toolCallId,
            content: result,
        });

        setPendingModeRequest(null);
        setIsLoading(true);
        agent.runAgent({ tools: getToolDefs() }).catch(handleRunError);
    };

    const toggleMode = (mode: string) => {
        const prev = activeModeRef.current;
        if (prev === mode) return;
        activeModeRef.current = mode;
        setActiveMode(mode);

        setAiContextMode(contextId, mode).catch(() => {
            activeModeRef.current = prev;
            setActiveMode(prev);
            appendError("Failed to switch mode");
        });
    };

    const abortRun = () => agentRef.current?.abortRun();

    return {
        chatMessages,
        isLoading,
        isInterrupted,
        inFlightToolCalls,
        reasoningPhase,
        reasoningText,
        pendingQuestion,
        pendingModeRequest,
        activeMode,
        turnActivity: turnActivityRef.current,
        handleSendMessage,
        handleQuestionAnswer,
        handleModeAnswer,
        toggleMode,
        abortRun,
        contextId,
    };
};
