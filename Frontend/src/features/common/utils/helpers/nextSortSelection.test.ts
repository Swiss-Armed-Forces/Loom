import { describe, expect, it } from "vitest";

import { SearchQuery } from "@features/common/utils/model";

import { nextSortSelection } from "./nextSortSelection";

const query = (
    sortField: string | null,
    sortDirection: "asc" | "desc" | null,
): SearchQuery => ({
    id: null,
    query: "",
    keepAlive: null,
    sortField,
    sortDirection,
    sortId: null,
    pageSize: null,
});

describe("nextSortSelection", () => {
    it("starts a field it does not sort by at descending", () => {
        expect(nextSortSelection(query("size", "asc"), "created")).toEqual({
            sortField: "created",
            sortDirection: "desc",
        });
    });

    it("reverses the field it already sorts descending", () => {
        expect(nextSortSelection(query("created", "desc"), "created")).toEqual({
            sortField: "created",
            sortDirection: "asc",
        });
    });

    it("reverses back", () => {
        expect(nextSortSelection(query("created", "asc"), "created")).toEqual({
            sortField: "created",
            sortDirection: "desc",
        });
    });

    it("treats a query with no direction as descending", () => {
        // The query carries null until something sets a direction, and the
        // search bar's toggle shows "desc" for it - so a second click on the
        // column has to reverse rather than appear to do nothing.
        expect(nextSortSelection(query("created", null), "created")).toEqual({
            sortField: "created",
            sortDirection: "asc",
        });
    });

    it("sorts descending when there is no query at all", () => {
        expect(nextSortSelection(null, "created")).toEqual({
            sortField: "created",
            sortDirection: "desc",
        });
    });
});
