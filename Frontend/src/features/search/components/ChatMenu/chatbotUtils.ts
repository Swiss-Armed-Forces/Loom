import type { Message } from "@ag-ui/client";

import type {
    ActivityRecord,
    ChatCitation,
    ChatMessage,
} from "./ChatWindow.types";

export const getToolLabel = (
    t: (key: string) => string,
    toolName: string,
): string => {
    const key = `chatbot.toolLabels.${toolName}`;
    const label = t(key);
    return label === key ? toolName : label;
};

export const createErrorMessage = (text: string): ChatMessage => ({
    text,
    isUser: false,
    citations: [],
    isError: true,
});

export const extractText = (m: Readonly<Message>): string =>
    typeof m.content === "string"
        ? m.content
        : Array.isArray(m.content)
          ? m.content
                .filter(
                    (p): p is { type: "text"; text: string } =>
                        p.type === "text",
                )
                .map((p) => p.text)
                .join(" ")
          : "";

export const mapToChatMessages = (
    messages: ReadonlyArray<Readonly<Message>>,
    citations: Record<string, ChatCitation[]>,
    activity: Record<string, ActivityRecord[]>,
    finalMsgIds: Set<string>,
): ChatMessage[] => {
    const result: ChatMessage[] = [];

    for (const m of messages) {
        if (m.role === "user") {
            const text = extractText(m);
            if (text) {
                result.push({
                    id: m.id,
                    text,
                    isUser: true,
                    citations: [],
                });
            }
            continue;
        }

        // Only show assistant messages explicitly marked as "real" final
        // messages (via TextMessageStartEvent or history restoration).
        // All intermediate protocol messages (tool-call rounds) are hidden.
        if (m.role !== "assistant" || !finalMsgIds.has(m.id)) continue;

        const text = extractText(m);
        const msgActivity = activity[m.id];
        if (!text && !msgActivity?.length) continue;

        result.push({
            id: m.id,
            text,
            isUser: false,
            citations: citations[m.id] ?? [],
            activity:
                msgActivity && msgActivity.length > 0 ? msgActivity : undefined,
        });
    }

    return result;
};
