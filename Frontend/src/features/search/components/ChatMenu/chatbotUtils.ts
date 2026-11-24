import type { Interrupt, Message, ResumeEntry } from "@ag-ui/client";

import type {
    ActivityRecord,
    ChatCitation,
    ChatMessage,
    PendingApproval,
    ToolCallRecord,
} from "./ChatWindow.types";

/**
 * Looks a name up in a translation block, falling back to the name itself.
 *
 * Both blocks are keyed on names the backend owns — tool names and bulk action
 * ids — so a name arriving without a translation is expected rather than a bug,
 * and showing it raw is better than showing the key.
 */
export const translateWithFallback = (
    t: (key: string) => string,
    namespace: string,
    name: string,
): string => {
    const key = `chatbot.${namespace}.${name}`;
    const label = t(key);
    return label === key ? name : label;
};

export const getToolLabel = (
    t: (key: string) => string,
    toolName: string,
): string => translateWithFallback(t, "toolLabels", toolName);

export const getBulkActionLabel = (
    t: (key: string) => string,
    action: string,
): string => translateWithFallback(t, "bulkActions", action);

/**
 * Reads a bulk action out of an interrupt's metadata, which the backend fills
 * with what the call covers rather than with the arguments the agent passed.
 */
export const toPendingApproval = (interrupt: Interrupt): PendingApproval => {
    const metadata: Record<string, unknown> = interrupt.metadata ?? {};
    return {
        id: interrupt.id,
        approvalId:
            typeof metadata.approval_id === "string"
                ? metadata.approval_id
                : "",
        action: typeof metadata.action === "string" ? metadata.action : "",
        queryString:
            typeof metadata.query_string === "string"
                ? metadata.query_string
                : "",
        matchedFiles:
            typeof metadata.matched_files === "number"
                ? metadata.matched_files
                : 0,
        message: interrupt.message ?? "",
    };
};

/**
 * Encodes one decision per interrupt for `buildResumeArray`.
 *
 * A decision the panel never took is a denial: the backend turns that into a
 * ToolDenied and the tool is never invoked, which is the safe answer for a write
 * with no undo.
 */
export const buildApprovalResponses = (
    interrupts: Interrupt[],
    decisions: Record<string, boolean>,
): Record<string, { status: "resolved"; payload: { approved: boolean } }> =>
    Object.fromEntries(
        interrupts.map((interrupt) => [
            interrupt.id,
            {
                status: "resolved" as const,
                payload: { approved: decisions[interrupt.id] === true },
            },
        ]),
    );

/**
 * Names the approval each answer is answering.
 *
 * The backend mints an id per question and will only dispatch an action whose
 * id comes back with the answer, so an approval is spent by the panel that was
 * shown it rather than by a request that merely addresses the same call. The
 * id is routing, not an answer, so it rides in `metadata` beside the payload.
 */
export const withApprovalIds = (
    entries: ResumeEntry[],
    approvalIds: Record<string, string>,
): ResumeEntry[] =>
    entries.map((entry) => {
        const approvalId = approvalIds[entry.interruptId];
        return approvalId === undefined
            ? entry
            : { ...entry, metadata: { ...entry.metadata, approvalId } };
    });

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

/** The assistant messages of one answer, while they are being collected. */
interface AssistantTurn {
    /** The first assistant message of the turn, which names the bubble. */
    id: string;
    /** The text of each assistant message that carried any. */
    segments: string[];
    streaming: boolean;
}

/**
 * Rebuilds the rendered message list, reusing the object from `previous`
 * whenever a message is unchanged.
 *
 * One answer is one bubble. The agent writes an assistant message per model
 * response, so a question that takes two tool calls to answer arrives as three
 * of them, and the ones that opened with a tool call carry no text at all — a
 * tool call names a parent message, so there is one even when the model wrote
 * nothing. They are all the same answer, so every assistant message up to the
 * next user message is folded into one bubble, keyed on the first of them.
 * That key is also what the turn's activity and citations are gathered under.
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

    let turn: AssistantTurn | null = null;
    const closeTurn = (): void => {
        if (turn === null) return;
        const text = turn.segments.join("\n\n");
        const turnActivity = activity[turn.id];
        if (text || turnActivity?.length) {
            push({
                id: turn.id,
                text,
                isUser: false,
                citations: citations[turn.id] ?? EMPTY_CITATIONS,
                activity: turnActivity?.length ? turnActivity : undefined,
                isStreaming: turn.streaming,
            });
        }
        turn = null;
    };

    for (const m of messages) {
        if (m.role === "user") {
            closeTurn();
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
        // A reasoning or tool message sits inside a turn rather than ending
        // one, and neither is a bubble of its own.
        if (m.role !== "assistant") continue;

        turn ??= { id: m.id, segments: [], streaming: false };
        const text = extractText(m);
        if (text) turn.segments.push(text);
        if (m.id === streamingMsgId) turn.streaming = true;
    }
    closeTurn();

    return result;
};
