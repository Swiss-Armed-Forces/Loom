export interface ChatCitation {
    id: string;
    fileId: string;
    text: string;
}

export interface ToolCallRecord {
    id: string;
    name: string;
    label: string;
    args: string;
    result: string;
    status: "running" | "done";
}

export interface ActivityRecord {
    type: "reasoning" | "tool_call";
    text?: string;
    toolCall?: ToolCallRecord;
}

export interface ChatMessage {
    id?: string;
    text: string;
    isUser: boolean;
    citations: ChatCitation[];
    isError?: boolean;
    activity?: ActivityRecord[];
    /** True while the agent is still writing this message's text. */
    isStreaming?: boolean;
}

export interface PendingQuestionPrompt {
    question: string;
    options: string[];
}

/**
 * One backend action the agent run is paused on until the user answers.
 *
 * The backend raises the approval from inside the tool, so the pause is a
 * property of the action rather than something the agent chose to ask about.
 */
export interface PendingApproval {
    /** AG-UI interrupt id — what a resume entry is addressed to. */
    id: string;
    /**
     * The backend's id for this approval, sent back with the answer.
     *
     * It names the one dispatch the answer buys, and the backend will not act
     * on an answer that leaves it out. Never shown to the user.
     */
    approvalId: string;
    /** The action being approved, e.g. `add_tags`. */
    action: string;
    /** The Lucene query the action covers. */
    queryString: string;
    /** How many files that query matches. */
    matchedFiles: number;
    /** What to show for an interrupt carrying no bulk action details. */
    message: string;
}

export interface ChatWindowProps {
    messages: ChatMessage[];
    isLoading: boolean;
    query: string | null;
    onSuggestedQuestion: (q: string) => void;
    pendingQuestion?: PendingQuestionPrompt | null;
    onQuestionAnswer?: (answer: string) => void;
    scrollContainerRef?: React.RefObject<HTMLDivElement | null>;
    turnActivity: ActivityRecord[];
    isTurnActive: boolean;
    reasoningText: string;
    reasoningPhase: "idle" | "thinking" | "done";
}

export const ALL_SUGGESTED_QUESTIONS = [
    "Find all PDF files",
    "Are there any spreadsheets in here?",
    "Search for invoices or receipts",
    "Show me the most recently added documents",
    "Find emails from a specific sender",
    "Open the newest document",
    "Are there any scanned images?",
    "Find anything mentioning a contract",
    "Search for meeting notes or agendas",
    "What's the oldest file in here?",
    "Find documents from a specific year",
    "Search for anything related to a budget",
    "Are there any reports?",
    "Find files in a foreign language and translate one",
    "Search for project proposals",
    "Tag all invoices with 'finance'",
    "Find the largest files",
    "Show me all image files",
    "Find anything that mentions a deadline",
    "Search for documents with a specific keyword",
];

export const MAX_VISIBLE_MESSAGES = 50;

export const MAX_CHIP_LABEL_LENGTH = 28;
