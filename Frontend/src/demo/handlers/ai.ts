import { http } from "msw";

import { DemoQueryError } from "../query";
import {
    getDocuments,
    scheduleDemoTimeout,
    searchDocuments,
} from "../repository";

import { sendToChannel } from "./channels";
import { error, json, parseBody, stringValue } from "./shared";

const contexts = new Map<string, string>();
const MAX_CONTEXTS = 20;

const rememberContext = (contextId: string, query: string): void => {
    if (contexts.size >= MAX_CONTEXTS) {
        const oldestContextId = contexts.keys().next().value;
        if (oldestContextId) contexts.delete(oldestContextId);
    }
    contexts.set(contextId, query);
};

const streamAnswer = (contextId: string, question: string): void => {
    const query = contexts.get(contextId) ?? "*";
    let relevant: ReturnType<typeof getDocuments> = [];
    try {
        relevant = searchDocuments(question);
    } catch {
        // Natural-language questions need not be valid query syntax.
    }
    const fallback = searchDocuments(query);
    const source = relevant[0] ?? fallback[0] ?? getDocuments()[0];
    const answer = source
        ? `Based on ${source.name}, ${source.summary}`
        : "The offline demo has no matching document for that question.";
    const tokens = answer.match(/\S+\s*/g) ?? [answer];
    tokens.forEach((token, index) => {
        const tokenId = crypto.randomUUID();
        scheduleDemoTimeout(
            () =>
                sendToChannel(contextId, {
                    type: "chatBotToken",
                    token_id: tokenId,
                    token,
                }),
            45 * (index + 1),
        );
    });
    if (source) {
        scheduleDemoTimeout(
            () =>
                sendToChannel(contextId, {
                    type: "chatBotCitation",
                    id: crypto.randomUUID(),
                    file_id: source.id,
                    text: source.summary,
                    rank: 1,
                }),
            45 * (tokens.length + 1),
        );
    }
    scheduleDemoTimeout(
        () => sendToChannel(contextId, { type: "chatBotAnswerComplete" }),
        45 * (tokens.length + 2),
    );
};

const createContextHandler = http.post(
    /\/api\/v1\/ai$/,
    async ({ request }) => {
        const parsed = await parseBody(request);
        if (!parsed.ok) return parsed.response;
        const searchString = stringValue(parsed.value.search_string) ?? "*";
        try {
            searchDocuments(searchString);
        } catch (reason) {
            return error(
                reason instanceof DemoQueryError
                    ? reason.message
                    : "Invalid AI context query",
                400,
            );
        }
        const contextId = crypto.randomUUID();
        rememberContext(contextId, searchString);
        return json({ context_id: contextId });
    },
);

const questionHandler = http.post(
    /\/api\/v1\/ai\/([^/]+)\/process_question$/,
    async ({ request }) => {
        const match = new URL(request.url).pathname.match(
            /\/ai\/([^/]+)\/process_question$/,
        );
        const contextId = decodeURIComponent(match?.[1] ?? "");
        if (!contexts.has(contextId)) return error("AI context not found", 404);
        const parsed = await parseBody(request);
        if (!parsed.ok) return parsed.response;
        const question = stringValue(parsed.value.question);
        if (!question) return error("question is required", 422);
        streamAnswer(contextId, question);
        return json({ context_id: contextId }, 202);
    },
);

export const resetAiState = (): void => contexts.clear();

export const aiHandlers = [createContextHandler, questionHandler];
