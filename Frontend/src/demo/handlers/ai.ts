import { http, HttpResponse } from "msw";

import { getDocuments, searchDocuments } from "../repository";

import { empty, error, json, parseBody, stringValue } from "./shared";

interface DemoQuestion {
    question: string;
    answer: string;
    citations: { file_id: string; text: string }[];
    activity: {
        type: string;
        tool_name: string | null;
        text: string | null;
        input?: Record<string, unknown>;
        output: string | null;
    }[];
}

interface DemoConversation {
    contextId: string;
    createdAt: string;
    questions: DemoQuestion[];
    activeCapabilities: Set<string>;
}

const conversations = new Map<string, DemoConversation>();
const MAX_CONTEXTS = 20;

const extractContextId = (url: string): string => {
    const match = new URL(url).pathname.match(/\/ai\/([^/]+)/);
    return decodeURIComponent(match?.[1] ?? "");
};

const findSource = (question: string) => {
    let relevant: ReturnType<typeof getDocuments> = [];
    try {
        relevant = searchDocuments(question);
    } catch {
        // Natural-language questions need not be valid query syntax.
    }
    const fallback = getDocuments();
    return relevant[0] ?? fallback[0];
};

const buildAnswer = (
    source: ReturnType<typeof getDocuments>[number] | undefined,
) =>
    source
        ? `Based on ${source.name}, ${source.summary}`
        : "The interactive demo has no matching document for that question.";

const sseEvent = (event: Record<string, unknown>): string =>
    `data: ${JSON.stringify(event)}\n\n`;

const createContextHandler = http.post(/\/api\/v1\/ai$/, () => {
    const contextId = crypto.randomUUID();
    if (conversations.size >= MAX_CONTEXTS) {
        const oldestId = conversations.keys().next().value;
        if (oldestId) conversations.delete(oldestId);
    }
    conversations.set(contextId, {
        contextId,
        createdAt: new Date().toISOString(),
        questions: [],
        activeCapabilities: new Set(),
    });
    return json({ context_id: contextId });
});

const listContextsHandler = http.get(/\/api\/v1\/ai$/, () => {
    const contexts = [...conversations.values()].map((c) => ({
        context_id: c.contextId,
        created_at: c.createdAt,
        first_question: c.questions[0]?.question,
        question_count: c.questions.length,
    }));
    return json({ contexts });
});

const historyHandler = http.get(
    /\/api\/v1\/ai\/([^/]+)\/history$/,
    ({ request }) => {
        const contextId = extractContextId(request.url);
        const conv = conversations.get(contextId);
        if (!conv) return error("AI context not found", 404);
        return json({
            created_at: conv.createdAt,
            questions: conv.questions.map((q) => ({
                question: q.question,
                answer: q.answer,
                citations: q.citations,
                activity: q.activity,
            })),
            active_capabilities: [...conv.activeCapabilities],
        });
    },
);

const deleteContextHandler = http.delete(
    /\/api\/v1\/ai\/([^/]+)$/,
    ({ request }) => {
        const contextId = extractContextId(request.url);
        conversations.delete(contextId);
        return empty(204);
    },
);

const capabilitiesHandler = http.patch(
    /\/api\/v1\/ai\/([^/]+)\/capabilities$/,
    async ({ request }) => {
        const contextId = extractContextId(request.url);
        const conv = conversations.get(contextId);
        if (!conv) return error("AI context not found", 404);
        const parsed = await parseBody(request);
        if (!parsed.ok) return parsed.response;
        const capability = stringValue(parsed.value.capability);
        const active = parsed.value.active;
        if (!capability || typeof active !== "boolean")
            return error("capability and active are required", 422);
        if (active) {
            conv.activeCapabilities.add(capability);
        } else {
            conv.activeCapabilities.delete(capability);
        }
        return json({ ok: true });
    },
);

const DELAY_MS = 40;

const runHandler = http.post(
    /\/api\/v1\/ai\/([^/]+)\/run$/,
    async ({ request }) => {
        const contextId = extractContextId(request.url);
        const conv = conversations.get(contextId);
        if (!conv) return error("AI context not found", 404);

        let question = "";
        try {
            const body = (await request.json()) as Record<string, unknown>;
            const messages = body.messages as
                { role: string; content: string }[] | undefined;
            if (messages) {
                const userMessages = messages.filter((m) => m.role === "user");
                question = userMessages[userMessages.length - 1]?.content ?? "";
            }
        } catch {
            // Fall through with empty question.
        }

        const source = findSource(question);
        const answer = buildAnswer(source);
        const tokens = answer.match(/\S+\s*/g) ?? [answer];
        const deepSearch = conv.activeCapabilities.has("research_mode");

        const citation = source
            ? { file_id: source.id, text: source.summary }
            : undefined;

        const messageId = crypto.randomUUID();
        const runId = crypto.randomUUID();
        const reasoningId = crypto.randomUUID();

        const reasoningText = source
            ? `Looking at the available documents to find information relevant to "${question || "this query"}". Found "${source.name}" which appears to contain relevant content.`
            : `Searching through the available documents for "${question || "this query"}".`;

        const activity: DemoQuestion["activity"] = [
            {
                type: "reasoning",
                tool_name: null,
                text: reasoningText,
                output: null,
            },
        ];

        const stream = new ReadableStream({
            start(controller) {
                const encoder = new TextEncoder();
                const events: Record<string, unknown>[] = [];

                // RUN_STARTED
                events.push({
                    type: "RUN_STARTED",
                    threadId: contextId,
                    runId,
                });

                // Reasoning
                events.push({
                    type: "REASONING_START",
                    messageId: reasoningId,
                });
                events.push({
                    type: "REASONING_MESSAGE_START",
                    messageId: reasoningId,
                    role: "reasoning",
                });
                const reasoningTokens = reasoningText.match(/\S+\s*/g) ?? [
                    reasoningText,
                ];
                for (const token of reasoningTokens) {
                    events.push({
                        type: "REASONING_MESSAGE_CONTENT",
                        messageId: reasoningId,
                        delta: token,
                    });
                }
                events.push({
                    type: "REASONING_MESSAGE_END",
                    messageId: reasoningId,
                });
                events.push({
                    type: "REASONING_END",
                    messageId: reasoningId,
                });

                // Tool call: rag_search (always runs)
                const ragId = crypto.randomUUID();
                events.push({
                    type: "TOOL_CALL_START",
                    toolCallId: ragId,
                    toolCallName: "rag_search",
                });
                events.push({
                    type: "TOOL_CALL_ARGS",
                    toolCallId: ragId,
                    delta: JSON.stringify({ query: question || "*" }),
                });
                events.push({
                    type: "TOOL_CALL_END",
                    toolCallId: ragId,
                });
                const ragResult = JSON.stringify(
                    source
                        ? {
                              status: "ok",
                              hits: 1,
                              documents: [
                                  {
                                      file_id: source.id,
                                      name: source.name,
                                      score: 0.92,
                                      snippet: source.summary.slice(0, 120),
                                  },
                              ],
                          }
                        : { status: "ok", hits: 0, documents: [] },
                );
                events.push({
                    type: "TOOL_CALL_RESULT",
                    messageId: crypto.randomUUID(),
                    toolCallId: ragId,
                    role: "tool",
                    content: ragResult,
                });
                activity.push({
                    type: "tool_call",
                    tool_name: "rag_search",
                    text: null,
                    input: { query: question || "*" },
                    output: ragResult,
                });

                if (deepSearch) {
                    // Tool call: suggest_queries
                    const tc1Id = crypto.randomUUID();
                    events.push({
                        type: "TOOL_CALL_START",
                        toolCallId: tc1Id,
                        toolCallName: "suggest_queries",
                    });
                    events.push({
                        type: "TOOL_CALL_ARGS",
                        toolCallId: tc1Id,
                        delta: JSON.stringify({ question }),
                    });
                    events.push({
                        type: "TOOL_CALL_END",
                        toolCallId: tc1Id,
                    });
                    const suggestResult = JSON.stringify({
                        queries: [
                            question || "*",
                            `${question || "*"} summary`,
                            `${question || "*"} details`,
                        ],
                    });
                    events.push({
                        type: "TOOL_CALL_RESULT",
                        messageId: crypto.randomUUID(),
                        toolCallId: tc1Id,
                        role: "tool",
                        content: suggestResult,
                    });
                    activity.push({
                        type: "tool_call",
                        tool_name: "suggest_queries",
                        text: null,
                        input: { question },
                        output: suggestResult,
                    });

                    // Tool call: execute_query
                    const tc2Id = crypto.randomUUID();
                    events.push({
                        type: "TOOL_CALL_START",
                        toolCallId: tc2Id,
                        toolCallName: "execute_query",
                    });
                    events.push({
                        type: "TOOL_CALL_ARGS",
                        toolCallId: tc2Id,
                        delta: JSON.stringify({
                            query: question || "*",
                        }),
                    });
                    events.push({
                        type: "TOOL_CALL_END",
                        toolCallId: tc2Id,
                    });
                    const executeResult = JSON.stringify(
                        source
                            ? {
                                  total: 1,
                                  results: [
                                      {
                                          file_id: source.id,
                                          name: source.name,
                                          score: 0.89,
                                      },
                                  ],
                              }
                            : { total: 0, results: [] },
                    );
                    events.push({
                        type: "TOOL_CALL_RESULT",
                        messageId: crypto.randomUUID(),
                        toolCallId: tc2Id,
                        role: "tool",
                        content: executeResult,
                    });
                    activity.push({
                        type: "tool_call",
                        tool_name: "execute_query",
                        text: null,
                        input: { query: question || "*" },
                        output: executeResult,
                    });
                }

                // TEXT_MESSAGE_START
                events.push({
                    type: "TEXT_MESSAGE_START",
                    messageId,
                    role: "assistant",
                });

                // TEXT_MESSAGE_CONTENT — one event per token
                for (const token of tokens) {
                    events.push({
                        type: "TEXT_MESSAGE_CONTENT",
                        messageId,
                        delta: token,
                    });
                }

                // CUSTOM citation
                if (citation) {
                    events.push({
                        type: "CUSTOM",
                        name: "citation",
                        value: citation,
                    });
                }

                // TEXT_MESSAGE_END
                events.push({
                    type: "TEXT_MESSAGE_END",
                    messageId,
                });

                // RUN_FINISHED
                events.push({
                    type: "RUN_FINISHED",
                    threadId: contextId,
                    runId,
                });

                // Store the Q&A in conversation history
                conv.questions.push({
                    question,
                    answer,
                    citations: citation ? [citation] : [],
                    activity,
                });

                // Emit events with delays for realistic streaming
                let index = 0;
                const timer = setInterval(() => {
                    if (index >= events.length) {
                        clearInterval(timer);
                        controller.close();
                        return;
                    }
                    controller.enqueue(encoder.encode(sseEvent(events[index])));
                    index++;
                }, DELAY_MS);
            },
        });

        return new HttpResponse(stream, {
            headers: {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                Connection: "keep-alive",
            },
        });
    },
);

export const resetAiState = (): void => conversations.clear();

export const aiHandlers = [
    createContextHandler,
    listContextsHandler,
    historyHandler,
    deleteContextHandler,
    capabilitiesHandler,
    runHandler,
];
