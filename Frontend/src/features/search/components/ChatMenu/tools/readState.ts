import type { PassiveFrontendTool, StateAccessor } from "./types";

const MAX_KEYS = 50;
const MAX_ARRAY_ITEMS = 50;
const ARRAY_PREVIEW_COUNT = 10;

const truncateValue = (value: unknown): unknown => {
    if (Array.isArray(value)) {
        if (value.length > MAX_ARRAY_ITEMS) {
            return {
                _truncated: true,
                length: value.length,
                first: value.slice(0, ARRAY_PREVIEW_COUNT).map(truncateValue),
            };
        }
        return value.map(truncateValue);
    }
    if (value !== null && typeof value === "object") {
        const keys = Object.keys(value);
        if (keys.length > MAX_KEYS) {
            return {
                _truncated: true,
                keyCount: keys.length,
                keys,
            };
        }
        const out: Record<string, unknown> = {};
        for (const k of keys) {
            out[k] = truncateValue((value as Record<string, unknown>)[k]);
        }
        return out;
    }
    return value;
};

export const createReadStateTool = (
    getState: StateAccessor,
): PassiveFrontendTool => ({
    interactive: false,
    definition: {
        name: "read_state",
        description:
            "Read a specific value from the UI state of the user you are talking to. " +
            "Use this to find out what the user is currently seeing — e.g. their active " +
            "search query, which file they have highlighted, how many results are shown, " +
            "or which tabs are open. Accepts a dot-separated path into the state tree; " +
            "supports numeric indices for arrays (e.g. 'search.filesInView.0'). " +
            "Large objects (>50 keys) return keys only; large arrays (>50 items) " +
            "return length and first 10 items. Use discover_state first to find available paths.",
        parameters: {
            type: "object",
            properties: {
                path: {
                    type: "string",
                    description:
                        "Dot-separated path into the state tree, e.g. 'search.highlightedFileId'",
                },
            },
            required: ["path"],
        },
    },
    handler: async (args) => {
        const path = String(args.path ?? "");
        if (!path) {
            return JSON.stringify({
                error: "Missing required parameter: path",
            });
        }

        const segments = path.split(".");
        let current: unknown = getState();

        for (const segment of segments) {
            if (current === null || current === undefined) {
                return JSON.stringify({
                    error: `Path '${path}' not found: reached null/undefined at '${segment}'`,
                });
            }
            if (typeof current !== "object") {
                return JSON.stringify({
                    error: `Path '${path}' not found: '${segment}' is not an object`,
                });
            }

            const asRecord = current as Record<string, unknown>;
            const index = Number(segment);
            if (Array.isArray(current) && !isNaN(index)) {
                current = current[index];
            } else if (segment in asRecord) {
                current = asRecord[segment];
            } else {
                return JSON.stringify({
                    error: `Path '${path}' not found: key '${segment}' does not exist`,
                    availableKeys: Object.keys(asRecord).slice(0, 20),
                });
            }
        }

        return JSON.stringify({ path, value: truncateValue(current) });
    },
});
