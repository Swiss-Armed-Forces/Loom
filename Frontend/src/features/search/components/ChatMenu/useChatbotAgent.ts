import { buildResumeArray, HttpAgent } from "@ag-ui/client";
import type {
    AgentSubscriber,
    Interrupt,
    ResumeEntry,
    Tool,
} from "@ag-ui/client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { getContextHistory, setAiContextMode } from "@app/api";
import { apiConfiguration } from "@app/api/apiConfiguration";
import { store } from "@app/store";

import {
    buildApprovalResponses,
    createErrorMessage,
    getToolLabel,
    mapToChatMessages,
    replaceToolCall,
    replaceToolCallInActivityMap,
    toPendingApproval,
    withApprovalIds,
} from "./chatbotUtils";
import type {
    ActivityRecord,
    ChatCitation,
    ChatMessage,
    PendingApproval,
    ToolCallRecord,
} from "./ChatWindow.types";
import { createFrontendTools } from "./tools";

export interface UseChatbotAgentResult {
    chatMessages: ChatMessage[];
    isLoading: boolean;
    reasoningPhase: "idle" | "thinking" | "done";
    reasoningText: string;
    pendingQuestion: PendingQuestion;
    pendingModeRequest: PendingModeRequest;
    pendingApprovals: PendingApproval[];
    activeMode: string;
    turnActivity: ActivityRecord[];
    isTurnActive: boolean;
    handleSendMessage: (text: string) => Promise<void>;
    handleQuestionAnswer: (answer: string) => void;
    handleModeAnswer: (allow: boolean) => Promise<void>;
    handleApprovalAnswer: (interruptId: string, approved: boolean) => void;
    toggleMode: (mode: string) => void;
    abortRun: () => void;
    contextId: string;
}

const NO_ACTIVITY: ActivityRecord[] = [];

type PendingQuestion = {
    toolCallId: string;
    question: string;
    options: string[];
} | null;

type PendingModeRequest = {
    toolCallId: string;
    mode: string;
    reason: string;
} | null;

export const useChatbotAgent = (
    contextId: string,
    onRunComplete: () => void,
): UseChatbotAgentResult => {
    const { t } = useTranslation();
    const onRunCompleteRef = useRef(onRunComplete);
    onRunCompleteRef.current = onRunComplete;

    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [reasoningText, setReasoningText] = useState("");
    const [reasoningPhase, setReasoningPhase] = useState<
        "idle" | "thinking" | "done"
    >("idle");
    const reasoningTextRef = useRef("");
    const [pendingApprovals, setPendingApprovals] = useState<PendingApproval[]>(
        [],
    );
    // The interrupts the panel's decisions are addressed to. buildResumeArray demands
    // a response for every one of them, so the run only resumes once each has one.
    const openInterruptsRef = useRef<Interrupt[]>([]);
    const approvalDecisionsRef = useRef<Record<string, boolean>>({});
    const [pendingQuestion, setPendingQuestionState] =
        useState<PendingQuestion>(null);
    const pendingQuestionRef = useRef<PendingQuestion>(null);
    const [activeMode, setActiveMode] = useState<string>("work");
    const activeModeRef = useRef<string>("work");
    const [pendingModeRequest, setPendingModeRequestState] =
        useState<PendingModeRequest>(null);
    const pendingModeRequestRef = useRef<PendingModeRequest>(null);

    // Each prompt is mirrored into a ref because the run can only continue once every
    // open one has been answered, and the handler that answers the last one has to see
    // the others as they are now rather than as they were when it was rendered.
    const setPendingQuestion = (next: PendingQuestion) => {
        pendingQuestionRef.current = next;
        setPendingQuestionState(next);
    };
    const setPendingModeRequest = (next: PendingModeRequest) => {
        pendingModeRequestRef.current = next;
        setPendingModeRequestState(next);
    };

    /** Whether the run is still waiting on an answer the user has not given. */
    const hasOpenPrompt = () =>
        pendingQuestionRef.current !== null ||
        pendingModeRequestRef.current !== null ||
        openInterruptsRef.current.some(
            (interrupt) => !(interrupt.id in approvalDecisionsRef.current),
        );
    const agentRef = useRef<HttpAgent | null>(null);
    // The message of the turn being run. Its id outlives the end of its text,
    // because the citations that belong to it arrive after it.
    const streamingMsgIdRef = useRef<string | null>(null);
    const isTextStreamingRef = useRef(false);
    const finalMsgIdsRef = useRef<Set<string>>(new Set());

    // Citations and per-message activity are the inputs mapToChatMessages
    // compares by reference, so they are always replaced, never mutated. They
    // are held in refs because the agent's event handlers read them
    // synchronously; `refreshChatMessages` pushes the result into state.
    const citationsRef = useRef<Record<string, ChatCitation[]>>({});
    const activityRef = useRef<Record<string, ActivityRecord[]>>({});

    // The activity of the turn currently running, shown live above the answer.
    const [turnActivity, setTurnActivityState] =
        useState<ActivityRecord[]>(NO_ACTIVITY);
    const turnActivityRef = useRef<ActivityRecord[]>(NO_ACTIVITY);
    const [isTurnActive, setIsTurnActive] = useState(false);

    // Working buffer for tool calls whose arguments are still streaming. Only
    // snapshots of these ever reach the rendered activity lists.
    const runToolCallsRef = useRef<Record<string, ToolCallRecord>>({});

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
    const errorHandledRef = useRef(false);

    const getToolDefs = () => frontendToolDefsRef.current;

    const setTurnActivity = useCallback((next: ActivityRecord[]) => {
        turnActivityRef.current = next;
        setTurnActivityState(next);
    }, []);

    /**
     * Re-derives the rendered list from the agent's messages. Passing the
     * previous list lets `mapToChatMessages` hand back the objects that did
     * not change, so only the affected bubbles re-render.
     */
    const refreshChatMessages = useCallback(() => {
        const agent = agentRef.current;
        if (!agent) return;
        setChatMessages((prev) =>
            mapToChatMessages(
                agent.messages,
                citationsRef.current,
                activityRef.current,
                finalMsgIdsRef.current,
                prev,
                isTextStreamingRef.current ? streamingMsgIdRef.current : null,
            ),
        );
    }, []);

    /**
     * Records a change to a tool call and republishes it everywhere it is
     * rendered — the live turn, and the message it was committed to once the
     * answer started streaming.
     */
    const updateToolCall = useCallback(
        (toolCallId: string, patch: Partial<ToolCallRecord>) => {
            const record = runToolCallsRef.current[toolCallId];
            if (!record) return;
            Object.assign(record, patch);
            const snapshot: ToolCallRecord = { ...record };

            const nextTurn = replaceToolCall(turnActivityRef.current, snapshot);
            if (nextTurn !== turnActivityRef.current) setTurnActivity(nextTurn);

            const nextActivity = replaceToolCallInActivityMap(
                activityRef.current,
                snapshot,
            );
            if (nextActivity !== activityRef.current) {
                activityRef.current = nextActivity;
                refreshChatMessages();
            }
        },
        [refreshChatMessages, setTurnActivity],
    );

    const appendError = useCallback((text: string) => {
        setChatMessages((prev) => [...prev, createErrorMessage(text)]);
        setIsLoading(false);
        setIsTurnActive(false);
    }, []);

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

                const restored: Parameters<HttpAgent["addMessage"]>[0][] = [];
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

                    restored.push({
                        role: "user",
                        id: crypto.randomUUID(),
                        content: q.question,
                    });
                    restored.push({
                        role: "assistant",
                        id: assistantMsgId,
                        content: q.answer,
                    });
                }
                // One notification for the whole history: addMessage schedules
                // its own async onMessagesChanged, so adding them one by one
                // would re-render the growing list once per restored message.
                // Anything sent before the history arrived keeps its place
                // after it.
                agent.setMessages([...restored, ...agent.messages]);
            },
        );

        const subscriber: AgentSubscriber = {
            onRunInitialized: () => {
                setIsLoading(true);
                setIsTurnActive(true);
                openInterruptsRef.current = [];
                approvalDecisionsRef.current = {};
                setPendingApprovals([]);
                runToolCallsRef.current = {};
                streamingMsgIdRef.current = null;
                isTextStreamingRef.current = false;
            },
            onToolCallStartEvent: ({ event }) => {
                const record: ToolCallRecord = {
                    id: event.toolCallId,
                    name: event.toolCallName,
                    label: getToolLabel(t, event.toolCallName),
                    args: "",
                    result: "",
                    status: "running",
                };
                runToolCallsRef.current[event.toolCallId] = record;
                setTurnActivity([
                    ...turnActivityRef.current,
                    { type: "tool_call", toolCall: { ...record } },
                ]);
            },
            onToolCallArgsEvent: ({ event }) => {
                // Arguments are not rendered while they stream, so this stays
                // on the working buffer and triggers no render.
                const record = runToolCallsRef.current[event.toolCallId];
                if (record) record.args += event.delta;
            },
            onToolCallResultEvent: ({ event }) => {
                updateToolCall(event.toolCallId, {
                    result: event.content,
                    status: "done",
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
                updateToolCall(event.toolCallId, { status: "done" });
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
                    setTurnActivity([
                        ...turnActivityRef.current,
                        { type: "reasoning", text: reasoningTextRef.current },
                    ]);
                }
                setReasoningPhase("done");
            },
            onRunFinishedEvent: (params) => {
                if (params.outcome !== "interrupt") return;
                openInterruptsRef.current = params.interrupts;
            },
            onRunErrorEvent: ({ event }) => {
                errorHandledRef.current = true;
                appendError(event.message ?? "Agent error");
            },
            onTextMessageStartEvent: ({ event }) => {
                streamingMsgIdRef.current = event.messageId;
                isTextStreamingRef.current = true;
                finalMsgIdsRef.current.add(event.messageId);
                setReasoningPhase("idle");
                // Hand the turn's activity over to the message it belongs to.
                // Tools still running keep updating in place from there.
                if (turnActivityRef.current.length > 0) {
                    activityRef.current = {
                        ...activityRef.current,
                        [event.messageId]: turnActivityRef.current,
                    };
                    setTurnActivity(NO_ACTIVITY);
                }
            },
            onTextMessageEndEvent: () => {
                // The answer is complete, so it is parsed as markdown whole.
                isTextStreamingRef.current = false;
                refreshChatMessages();
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
                refreshChatMessages();
            },
            onMessagesChanged: () => {
                refreshChatMessages();
            },
            onRunFinalized: () => {
                // A run that ends mid-answer — aborted, interrupted or
                // failed — sends no TEXT_MESSAGE_END, so what arrived of it
                // is settled here instead.
                const wasStreaming = isTextStreamingRef.current;
                isTextStreamingRef.current = false;
                if (wasStreaming || !errorHandledRef.current) {
                    refreshChatMessages();
                }
                errorHandledRef.current = false;
                // Without this the live turn keeps spinning after a run that
                // ended without an answer — an error, an interrupt, ask_user
                // or request_mode.
                setReasoningPhase("idle");
            },
            onRunFailed: () => {
                errorHandledRef.current = true;
                appendError("Cannot get a response");
            },
        };

        const { unsubscribe } = agent.subscribe(subscriber);

        return () => {
            abortController.abort();
            unsubscribe();
            agent.abortRun();
        };
    }, [
        contextId,
        t,
        appendError,
        refreshChatMessages,
        setTurnActivity,
        updateToolCall,
    ]);

    /**
     * Drives the run until it either finishes or stops on something the user has
     * to answer.
     *
     * `answered` names the interrupts `resume` responds to. They are restored when
     * the request carrying it never reaches the backend, because an approval the
     * panel has forgotten is one the run can never be given again.
     */
    const runAgentLoop = async (
        agent: HttpAgent,
        resume?: ResumeEntry[],
        answered?: Interrupt[],
    ) => {
        let resumeDelivered = resume === undefined;
        try {
            let nextResume = resume;
            while (true) {
                await agent.runAgent({
                    tools: getToolDefs(),
                    resume: nextResume,
                });
                resumeDelivered = true;
                nextResume = undefined;

                const pending = pendingFrontendToolsRef.current;
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

                for (const item of passiveItems) {
                    const tool = frontendToolsRef.current[item.toolName];
                    if (!tool || tool.interactive === true) continue;
                    const result = await tool.handler(item.args);

                    updateToolCall(item.toolCallId, {
                        result,
                        status: "done",
                    });

                    agent.addMessage({
                        role: "tool",
                        id: crypto.randomUUID(),
                        toolCallId: item.toolCallId,
                        content: result,
                    });
                }

                // The approvals and the interactive tools of the same turn are
                // raised together: one model response can hold a bulk action and
                // an ask_user, and both panels have to be offered before the
                // resumed request can carry the answers to either.
                const interrupts = openInterruptsRef.current;
                if (interrupts.length > 0) {
                    setPendingApprovals(interrupts.map(toPendingApproval));
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
                    } else {
                        setPendingModeRequest({
                            toolCallId: requestModeItem.toolCallId,
                            mode: requestedMode,
                            reason: String(requestModeItem.args.reason ?? ""),
                        });
                    }
                } else if (askUserItem) {
                    setPendingQuestion({
                        toolCallId: askUserItem.toolCallId,
                        question: String(askUserItem.args.question ?? ""),
                        options: Array.isArray(askUserItem.args.options)
                            ? (askUserItem.args.options as string[])
                            : [],
                    });
                }

                if (hasOpenPrompt()) {
                    setIsLoading(false);
                    return;
                }

                if (pending.length === 0) break;
            }
        } catch {
            if (!resumeDelivered && answered !== undefined) {
                openInterruptsRef.current = answered;
                approvalDecisionsRef.current = {};
                setPendingApprovals(answered.map(toPendingApproval));
            }
            if (!errorHandledRef.current) {
                appendError("Agent error");
            }
        }

        setIsLoading(false);
        setIsTurnActive(false);
        onRunCompleteRef.current();
    };

    /**
     * Carries the run on once nothing is left for the user to answer, handing
     * the backend the decisions taken on the interrupts it stopped at.
     */
    const continueRun = async (agent: HttpAgent) => {
        if (hasOpenPrompt()) return;

        const answered = openInterruptsRef.current;
        const resume =
            answered.length > 0
                ? withApprovalIds(
                      buildResumeArray(
                          answered,
                          buildApprovalResponses(
                              answered,
                              approvalDecisionsRef.current,
                          ),
                      ),
                      Object.fromEntries(
                          answered.map((interrupt) => [
                              interrupt.id,
                              toPendingApproval(interrupt).approvalId,
                          ]),
                      ),
                  )
                : undefined;

        openInterruptsRef.current = [];
        approvalDecisionsRef.current = {};
        setIsLoading(true);
        await runAgentLoop(
            agent,
            resume,
            answered.length > 0 ? answered : undefined,
        );
    };

    const handleSendMessage = async (text: string) => {
        const agent = agentRef.current;
        if (!agent) return;

        reasoningTextRef.current = "";
        setReasoningText("");
        setReasoningPhase("idle");
        setTurnActivity(NO_ACTIVITY);
        streamingMsgIdRef.current = null;
        isTextStreamingRef.current = false;
        errorHandledRef.current = false;

        agent.addMessage({
            role: "user",
            id: crypto.randomUUID(),
            content: text,
        });
        refreshChatMessages();

        await runAgentLoop(agent);
    };

    const handleQuestionAnswer = async (answer: string) => {
        const agent = agentRef.current;
        if (!agent || !pendingQuestion) return;
        const { toolCallId, question } = pendingQuestion;

        updateToolCall(toolCallId, { result: answer, status: "done" });

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
            setIsTurnActive(false);
            return;
        }
        await continueRun(agent);
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
        await continueRun(agent);
    };

    /**
     * Records one bulk action's decision and resumes the run once every prompt
     * the turn raised has been answered.
     *
     * Each action is decided on its own: a response holding two of them is two
     * writes the user has to agree to separately, and buildResumeArray needs an
     * answer for every interrupt before the run can be given any of them.
     */
    const handleApprovalAnswer = (interruptId: string, approved: boolean) => {
        const agent = agentRef.current;
        if (!agent || interruptId in approvalDecisionsRef.current) return;

        approvalDecisionsRef.current[interruptId] = approved;
        setPendingApprovals((prev) =>
            prev.filter((approval) => approval.id !== interruptId),
        );

        void continueRun(agent);
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
        reasoningPhase,
        reasoningText,
        pendingQuestion,
        pendingModeRequest,
        pendingApprovals,
        activeMode,
        turnActivity,
        isTurnActive,
        handleSendMessage,
        handleQuestionAnswer,
        handleModeAnswer,
        handleApprovalAnswer,
        toggleMode,
        abortRun,
        contextId,
    };
};
