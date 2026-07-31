import { beforeEach, describe, expect, it, vi } from "vitest";

import { searchSlice, updateQuery } from "./searchSlice";

const mockToastError = vi.hoisted(() => vi.fn());

vi.mock("i18next", () => ({
    t: (key: string) => key,
}));

vi.mock("react-toastify", () => ({
    toast: { error: mockToastError },
}));

describe("search query cancellation", () => {
    beforeEach(() => mockToastError.mockClear());

    it("ignores an intentionally aborted query", () => {
        const initialState = searchSlice.reducer(undefined, {
            type: "test/initialize",
        });

        const nextState = searchSlice.reducer(initialState, {
            type: updateQuery.rejected.type,
            meta: { aborted: true },
            payload: "cancelled",
        });

        expect(nextState).toBe(initialState);
        expect(mockToastError).not.toHaveBeenCalled();
    });

    it("still reports a genuine query failure", () => {
        const initialState = searchSlice.reducer(undefined, {
            type: "test/initialize",
        });

        const nextState = searchSlice.reducer(initialState, {
            type: updateQuery.rejected.type,
            meta: { aborted: false },
            payload: "search failed",
        });

        expect(nextState.queryError).toBe("search failed");
        expect(mockToastError).toHaveBeenCalledOnce();
    });
});
