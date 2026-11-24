import { configureStore } from "@reduxjs/toolkit";
import { act, renderHook } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { ReactNode } from "react";
import { Provider } from "react-redux";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";

import commonReducer from "@app/slices/commonSlice";
import searchReducer from "@app/slices/searchSlice";

import { useChatbotAgent } from "./useChatbotAgent";

/**
 * One question answered through one tool call, as the backend streams it.
 *
 * The empty TEXT_MESSAGE pair is not padding: the agent framework opens an
 * assistant message for a response that starts with a tool call, because the
 * call names a parent message and there has to be one in the stream. A round
 * of tool use therefore arrives as a text message carrying nothing at all.
 */
const EVENTS: Record<string, unknown>[] = [
    { type: "RUN_STARTED", threadId: "t1", runId: "r1" },
    { type: "REASONING_START", messageId: "re1" },
    { type: "REASONING_MESSAGE_START", messageId: "re1", role: "reasoning" },
    {
        type: "REASONING_MESSAGE_CONTENT",
        messageId: "re1",
        delta: "I should search the index.",
    },
    { type: "REASONING_MESSAGE_END", messageId: "re1" },
    { type: "REASONING_END", messageId: "re1" },
    { type: "TEXT_MESSAGE_START", messageId: "empty1", role: "assistant" },
    { type: "TEXT_MESSAGE_END", messageId: "empty1" },
    {
        type: "TOOL_CALL_START",
        toolCallId: "tc1",
        toolCallName: "search_files",
        parentMessageId: "empty1",
    },
    { type: "TOOL_CALL_ARGS", toolCallId: "tc1", delta: '{"q":"invoice"}' },
    { type: "TOOL_CALL_END", toolCallId: "tc1" },
    {
        type: "TOOL_CALL_RESULT",
        messageId: "tr1",
        toolCallId: "tc1",
        content: "3 hits",
        role: "tool",
    },
    { type: "REASONING_START", messageId: "re2" },
    { type: "REASONING_MESSAGE_START", messageId: "re2", role: "reasoning" },
    {
        type: "REASONING_MESSAGE_CONTENT",
        messageId: "re2",
        delta: "Three hits, that is the answer.",
    },
    { type: "REASONING_MESSAGE_END", messageId: "re2" },
    { type: "REASONING_END", messageId: "re2" },
    { type: "TEXT_MESSAGE_START", messageId: "ans", role: "assistant" },
    {
        type: "TEXT_MESSAGE_CONTENT",
        messageId: "ans",
        delta: "Here are the three invoices.",
    },
    { type: "TEXT_MESSAGE_END", messageId: "ans" },
    {
        type: "RUN_FINISHED",
        threadId: "t1",
        runId: "r1",
        outcome: { type: "success" },
    },
];

const eventStream = (): ReadableStream<Uint8Array> => {
    const encoder = new TextEncoder();
    return new ReadableStream({
        start(controller) {
            for (const event of EVENTS) {
                controller.enqueue(
                    encoder.encode(`data: ${JSON.stringify(event)}\n\n`),
                );
            }
            controller.close();
        },
    });
};

const server = setupServer(
    http.get(/\/api\/v1\/ai\/([^/]+)\/history$/, () =>
        HttpResponse.json({
            created_at: "2026-01-01T00:00:00Z",
            questions: [],
            active_mode: "work",
            hidden: false,
        }),
    ),
    http.post(
        /\/api\/v1\/ai\/([^/]+)\/run$/,
        () =>
            new HttpResponse(eventStream(), {
                headers: { "Content-Type": "text/event-stream" },
            }),
    ),
);

const wrapper = ({ children }: { children: ReactNode }) => (
    <Provider
        store={configureStore({
            reducer: { search: searchReducer, common: commonReducer },
        })}
    >
        {children}
    </Provider>
);

describe("useChatbotAgent", () => {
    beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
    afterEach(() => server.resetHandlers());
    afterAll(() => server.close());

    it("answers a tool-using question in one bubble carrying the whole turn", async () => {
        const { result } = renderHook(() => useChatbotAgent("ctx1", () => {}), {
            wrapper,
        });

        await act(async () => {
            await result.current.handleSendMessage("find invoices");
        });

        const assistant = result.current.chatMessages.filter((m) => !m.isUser);
        expect(assistant).toHaveLength(1);
        expect(assistant[0].text).toBe("Here are the three invoices.");

        // Both rounds' reasoning belongs to the answer, not only the last.
        expect(assistant[0].activity).toEqual([
            { type: "reasoning", text: "I should search the index." },
            {
                type: "tool_call",
                toolCall: expect.objectContaining({
                    name: "search_files",
                    status: "done",
                }),
            },
            { type: "reasoning", text: "Three hits, that is the answer." },
        ]);

        // Nothing is left running, so no timeline can be shown as active.
        expect(result.current.isTurnActive).toBe(false);
        expect(result.current.turnActivity).toEqual([]);
    });
});
