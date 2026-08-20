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
}

export interface ChatWindowProps {
    messages: ChatMessage[];
    isLoading: boolean;
    query: string | null;
    onSuggestedQuestion: (q: string) => void;
    isInterrupted: boolean;
    pendingQuestion?: { question: string; options: string[] } | null;
    onQuestionAnswer?: (answer: string) => void;
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
