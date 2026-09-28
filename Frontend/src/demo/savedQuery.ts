import type { CustomQuery } from "@app/slices/searchSlice";

const SEARCH_STATE_LOCAL_STORAGE_KEY = "SEARCH_STATE";

export const DEMO_SAVED_QUERY_ID = "loom-demo-interesting-documents";

export const DEMO_SAVED_QUERY = {
    id: DEMO_SAVED_QUERY_ID,
    query: {
        id: null,
        query: "tags:interesting",
        keepAlive: null,
        sortField: null,
        sortDirection: null,
        sortId: null,
        pageSize: null,
    },
    // Exactly one fixture is tagged "interesting"; the other two carry
    // "🤖 interesting", which `tags:interesting` does not match (see
    // repository.test.ts). Saved-query counts are now polled from app start
    // rather than only while the sidebar panel is open, so a seed that does not
    // match reality is visible as the badge changing shortly after load.
    fileCount: 1,
    lastSeenCount: 1,
    hasNewFiles: false,
    name: "Interesting documents",
    icon: "Stars",
} as const satisfies CustomQuery;

interface PersistedDemoSearchState {
    customQueries?: unknown;
    [key: string]: unknown;
}

// Deliberately does not require `lastSeenCount`: this guard runs before the
// store rehydrates, so demanding a field added later would delete a returning
// visitor's saved queries instead of letting normalizeCustomQueries backfill
// them.
const isCustomQuery = (value: unknown): value is CustomQuery => {
    if (value === null || typeof value !== "object" || Array.isArray(value))
        return false;
    const query = value as Partial<CustomQuery>;
    return (
        typeof query.id === "string" &&
        query.query !== null &&
        typeof query.query === "object" &&
        typeof query.fileCount === "number" &&
        typeof query.hasNewFiles === "boolean" &&
        typeof query.name === "string" &&
        typeof query.icon === "string"
    );
};

export const seedDemoSavedQuery = (storage: Storage): void => {
    let persistedState: PersistedDemoSearchState = {};
    const storedState = storage.getItem(SEARCH_STATE_LOCAL_STORAGE_KEY);

    if (storedState) {
        try {
            const parsedState = JSON.parse(storedState) as unknown;
            if (
                parsedState !== null &&
                typeof parsedState === "object" &&
                !Array.isArray(parsedState)
            ) {
                persistedState = parsedState as PersistedDemoSearchState;
            }
        } catch {
            persistedState = {};
        }
    }

    const existingQueries = Array.isArray(persistedState.customQueries)
        ? persistedState.customQueries.filter(
              (query): query is CustomQuery =>
                  isCustomQuery(query) && query.id !== DEMO_SAVED_QUERY_ID,
          )
        : [];

    storage.setItem(
        SEARCH_STATE_LOCAL_STORAGE_KEY,
        JSON.stringify({
            ...persistedState,
            customQueries: [...existingQueries, DEMO_SAVED_QUERY],
        }),
    );
};
