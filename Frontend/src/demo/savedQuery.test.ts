import { beforeEach, describe, expect, it } from "vitest";

import {
    DEMO_SAVED_QUERY,
    DEMO_SAVED_QUERY_ID,
    seedDemoSavedQuery,
} from "./savedQuery";

const SEARCH_STATE_LOCAL_STORAGE_KEY = "SEARCH_STATE";

const loadSearchState = () =>
    JSON.parse(
        window.localStorage.getItem(SEARCH_STATE_LOCAL_STORAGE_KEY) ?? "{}",
    ) as {
        customQueries?: unknown[];
        query?: { query: string };
    };

describe("demo saved query", () => {
    beforeEach(() => window.localStorage.clear());

    it("seeds the interesting-documents query", () => {
        seedDemoSavedQuery(window.localStorage);

        expect(loadSearchState().customQueries).toEqual([DEMO_SAVED_QUERY]);
    });

    it("restores the canonical query while preserving other search state", () => {
        window.localStorage.setItem(
            SEARCH_STATE_LOCAL_STORAGE_KEY,
            JSON.stringify({
                query: { query: "*" },
                customQueries: [
                    {
                        ...DEMO_SAVED_QUERY,
                        id: "visitor-query",
                        name: "Mine",
                    },
                    { id: DEMO_SAVED_QUERY_ID, name: "Changed" },
                    null,
                ],
            }),
        );

        seedDemoSavedQuery(window.localStorage);

        expect(loadSearchState()).toEqual({
            query: { query: "*" },
            customQueries: [
                {
                    ...DEMO_SAVED_QUERY,
                    id: "visitor-query",
                    name: "Mine",
                },
                DEMO_SAVED_QUERY,
            ],
        });
    });

    it("recovers from malformed persisted state", () => {
        window.localStorage.setItem(SEARCH_STATE_LOCAL_STORAGE_KEY, "not-json");

        seedDemoSavedQuery(window.localStorage);

        expect(loadSearchState().customQueries).toEqual([DEMO_SAVED_QUERY]);
    });
});
