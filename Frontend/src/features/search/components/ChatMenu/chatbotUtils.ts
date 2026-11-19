import type { Message } from "@ag-ui/client";

import type {
    ActivityRecord,
    ChatCitation,
    ChatMessage,
    ToolCallRecord,
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
    // Errors are the only messages not minted by the agent, and without an id
    // the list falls back to an index key, which remounts whole subtrees as
    // soon as the list shifts.
    id: crypto.randomUUID(),
    text,
    isUser: false,
    citations: [],
    isError: true,
});

/** An answer still being streamed, split at the last complete block. */
export interface StreamedMarkdown {
    /** The blocks that are already in their final shape. */
    stable: string;
    /** The block still being written. */
    tail: string;
}

/** The opening or closing line of a fenced code block. */
const FENCE = /^ {0,3}(`{3,}|~{3,})/;

/**
 * Splits a partially streamed answer at the last block boundary.
 *
 * Markdown is parsed block by block, so everything up to the last blank line
 * is settled and can be parsed once and kept; the block still being written is
 * rendered as plain text until the next blank line completes it. That makes
 * the parsing cost of an answer linear in its length instead of quadratic.
 *
 * A blank line inside a fenced code block is not a boundary: splitting there
 * leaves the fence unterminated, which flips the tail between a paragraph and
 * a code block on every token and re-lexes the block each time.
 */
export const splitStreamedMarkdown = (text: string): StreamedMarkdown => {
    let fence: string | null = null;
    let offset = 0;
    let boundary = 0;
    for (const line of text.split("\n")) {
        offset += line.length + 1;
        const marker = FENCE.exec(line)?.[1];
        if (fence === null && marker !== undefined) {
            fence = marker;
        } else if (
            fence !== null &&
            marker !== undefined &&
            marker[0] === fence[0] &&
            marker.length >= fence.length
        ) {
            fence = null;
        } else if (fence === null && line.trim() === "") {
            boundary = offset;
        }
    }
    return { stable: text.slice(0, boundary), tail: text.slice(boundary) };
};

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

const EMPTY_CITATIONS: ChatCitation[] = [];

/**
 * Returns an activity list with `toolCall` swapped in for the entry of the
 * same id, or the original list when it holds no such entry.
 *
 * Tool call records are published as snapshots rather than mutated, so that an
 * unchanged activity list keeps its reference and the messages holding it are
 * reused by `mapToChatMessages`.
 */
export const replaceToolCall = (
    activity: ActivityRecord[],
    toolCall: ToolCallRecord,
): ActivityRecord[] => {
    let changed = false;
    const next = activity.map((entry) => {
        if (entry.type !== "tool_call" || entry.toolCall?.id !== toolCall.id) {
            return entry;
        }
        changed = true;
        return { type: "tool_call" as const, toolCall };
    });
    return changed ? next : activity;
};

/** Applies {@link replaceToolCall} to every message's activity list. */
export const replaceToolCallInActivityMap = (
    activityByMessage: Record<string, ActivityRecord[]>,
    toolCall: ToolCallRecord,
): Record<string, ActivityRecord[]> => {
    let changed = false;
    const next: Record<string, ActivityRecord[]> = {};
    for (const [messageId, activity] of Object.entries(activityByMessage)) {
        const updated = replaceToolCall(activity, toolCall);
        if (updated !== activity) changed = true;
        next[messageId] = updated;
    }
    return changed ? next : activityByMessage;
};

/**
 * Citations and activity are replaced rather than mutated, so comparing them
 * by reference is enough to tell a message apart from its previous version.
 */
const isUnchanged = (
    previous: ChatMessage,
    next: Readonly<ChatMessage>,
): boolean =>
    previous.text === next.text &&
    previous.isUser === next.isUser &&
    previous.citations === next.citations &&
    previous.activity === next.activity &&
    previous.isStreaming === next.isStreaming;

/**
 * Rebuilds the rendered message list, reusing the object from `previous`
 * whenever a message is unchanged.
 *
 * The agent emits one message-changed event per streamed token, each carrying
 * the whole conversation. Allocating a fresh object per message would give
 * every bubble a new identity on every token, defeating `React.memo` and
 * re-parsing the markdown of the entire thread. Preserving identity keeps the
 * re-render to the message actually being streamed.
 */
export const mapToChatMessages = (
    messages: ReadonlyArray<Readonly<Message>>,
    citations: Record<string, ChatCitation[]>,
    activity: Record<string, ActivityRecord[]>,
    finalMsgIds: Set<string>,
    previous: ReadonlyArray<ChatMessage> = [],
    streamingMsgId: string | null = null,
): ChatMessage[] => {
    const previousById = new Map<string, ChatMessage>();
    for (const m of previous) {
        if (m.id !== undefined) previousById.set(m.id, m);
    }

    const result: ChatMessage[] = [];
    const push = (message: ChatMessage): void => {
        const before =
            message.id === undefined ? undefined : previousById.get(message.id);
        result.push(before && isUnchanged(before, message) ? before : message);
    };

    for (const m of messages) {
        if (m.role === "user") {
            const text = extractText(m);
            if (text) {
                push({
                    id: m.id,
                    text,
                    isUser: true,
                    citations: EMPTY_CITATIONS,
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

        push({
            id: m.id,
            text,
            isUser: false,
            citations: citations[m.id] ?? EMPTY_CITATIONS,
            activity:
                msgActivity && msgActivity.length > 0 ? msgActivity : undefined,
            isStreaming: m.id === streamingMsgId,
        });
    }

    return result;
};
