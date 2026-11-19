import type { Message } from "@ag-ui/client";
import { describe, expect, it } from "vitest";

import { mapToChatMessages, splitStreamedMarkdown } from "./chatbotUtils";
import type {
    ActivityRecord,
    ChatCitation,
    ToolCallRecord,
} from "./ChatWindow.types";

const user = (id: string, content: string): Message =>
    ({ id, role: "user", content }) as Message;

const assistant = (id: string, content: string): Message =>
    ({ id, role: "assistant", content }) as Message;

const toolCall = (status: ToolCallRecord["status"]): ActivityRecord => ({
    type: "tool_call",
    toolCall: {
        id: "call-1",
        name: "search",
        label: "Search",
        args: "{}",
        result: status === "done" ? "ok" : "",
        status,
    },
});

/** A three-turn conversation with the last assistant message still streaming. */
const conversation = (streamingText: string): Message[] => [
    user("u1", "first question"),
    assistant("a1", "first answer"),
    user("u2", "second question"),
    assistant("a2", "second answer"),
    user("u3", "third question"),
    assistant("a3", streamingText),
];

const finalIds = new Set(["a1", "a2", "a3"]);

describe("mapToChatMessages", () => {
    it("reuses every unchanged message when a token is appended", () => {
        const first = mapToChatMessages(
            conversation("a partial"),
            {},
            {},
            finalIds,
            [],
        );
        const second = mapToChatMessages(
            conversation("a partial answer"),
            {},
            {},
            finalIds,
            first,
        );

        expect(second).toHaveLength(first.length);

        // Everything before the streaming message keeps its identity, so
        // React.memo holds and their markdown is not re-parsed.
        for (let i = 0; i < first.length - 1; i++) {
            expect(second[i]).toBe(first[i]);
        }

        // Only the streaming message is rebuilt.
        const last = second[second.length - 1];
        expect(last).not.toBe(first[first.length - 1]);
        expect(last.text).toBe("a partial answer");
    });

    it("rebuilds a message when its tool call changes status", () => {
        const messages = conversation("answer");
        const running: Record<string, ActivityRecord[]> = {
            a3: [toolCall("running")],
        };
        const first = mapToChatMessages(messages, {}, running, finalIds, []);

        // The agent replaces the activity array rather than mutating the
        // record in place, which is what makes the reference check valid.
        const done: Record<string, ActivityRecord[]> = {
            a3: [toolCall("done")],
        };
        const second = mapToChatMessages(messages, {}, done, finalIds, first);

        const index = first.length - 1;
        expect(second[index]).not.toBe(first[index]);
        expect(second[index].activity?.[0].toolCall?.status).toBe("done");

        // Untouched messages are still reused.
        expect(second[0]).toBe(first[0]);
        expect(second[1]).toBe(first[1]);
    });

    it("rebuilds a message when a citation arrives for it", () => {
        const messages = conversation("answer");
        const first = mapToChatMessages(messages, {}, {}, finalIds, []);

        const citations: Record<string, ChatCitation[]> = {
            a3: [{ id: "f1", fileId: "f1", text: "a source" }],
        };
        const second = mapToChatMessages(
            messages,
            citations,
            {},
            finalIds,
            first,
        );

        const index = first.length - 1;
        expect(second[index]).not.toBe(first[index]);
        expect(second[index].citations).toHaveLength(1);
        expect(second[0]).toBe(first[0]);
    });

    it("reuses everything when nothing changed at all", () => {
        const messages = conversation("answer");
        const first = mapToChatMessages(messages, {}, {}, finalIds, []);
        const second = mapToChatMessages(messages, {}, {}, finalIds, first);

        second.forEach((m, i) => expect(m).toBe(first[i]));
    });

    it("hides assistant messages that are not marked final", () => {
        const result = mapToChatMessages(
            conversation("answer"),
            {},
            {},
            new Set(["a1"]),
            [],
        );

        expect(result.map((m) => m.id)).toEqual(["u1", "a1", "u2", "u3"]);
    });

    it("marks only the message whose text is still streaming", () => {
        const result = mapToChatMessages(
            conversation("a partial"),
            {},
            {},
            finalIds,
            [],
            "a3",
        );

        expect(result.map((m) => m.isStreaming)).toEqual([
            undefined,
            false,
            undefined,
            false,
            undefined,
            true,
        ]);
    });

    it("rebuilds the message when its stream ends", () => {
        const messages = conversation("the answer");
        const streaming = mapToChatMessages(
            messages,
            {},
            {},
            finalIds,
            [],
            "a3",
        );
        const settled = mapToChatMessages(
            messages,
            {},
            {},
            finalIds,
            streaming,
            null,
        );

        const index = streaming.length - 1;
        expect(settled[index]).not.toBe(streaming[index]);
        expect(settled[index].isStreaming).toBe(false);
    });
});

describe("splitStreamedMarkdown", () => {
    it("splits at the last blank line", () => {
        expect(splitStreamedMarkdown("done\n\nstill being wri")).toEqual({
            stable: "done\n\n",
            tail: "still being wri",
        });
    });

    it("keeps an answer with no complete block in the tail", () => {
        expect(splitStreamedMarkdown("a single parag")).toEqual({
            stable: "",
            tail: "a single parag",
        });
    });

    it("does not split inside a fenced code block", () => {
        const text = "intro\n\n```python\ndef f():\n\n    return 1\n";

        expect(splitStreamedMarkdown(text)).toEqual({
            stable: "intro\n\n",
            tail: "```python\ndef f():\n\n    return 1\n",
        });
    });

    it("splits again once the fence closes", () => {
        const text = "```\ncode\n```\n\nnext";

        expect(splitStreamedMarkdown(text)).toEqual({
            stable: "```\ncode\n```\n\n",
            tail: "next",
        });
    });
});
