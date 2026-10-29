import { describe, expect, it } from "vitest";

import { fileInViewChanged, searchSlice } from "@app/slices/searchSlice";
import type { RootState } from "@app/store";

import { createGetTheseFilesTool } from "./getTheseFiles";

type SearchStateSlice = ReturnType<typeof searchSlice.reducer>;

const emptySearchState = () =>
    searchSlice.reducer(undefined, { type: "test/initialize" });

/**
 * A query whose first page has already landed.
 *
 * Shaped like `updateQuery.fulfilled`'s payload rather than driven through the
 * thunk, which would need the network.
 */
const withResults = (count: number, totalFiles = count): SearchStateSlice =>
    searchSlice.reducer(emptySearchState(), {
        type: "updateQueryThunk/fulfilled",
        payload: {
            query: {
                id: "pit-1",
                query: "foo",
                keepAlive: null,
                sortField: null,
                sortDirection: null,
                sortId: null,
                pageSize: null,
            },
            files: Array.from({ length: count }, (_, i) => ({
                fileId: `f-${i}`,
                sortId: [i],
            })),
            totalFiles,
        },
    });

const scrolledTo = (state: SearchStateSlice, fileIds: string[]) =>
    fileIds.reduce(
        (acc, fileId) =>
            searchSlice.reducer(
                acc,
                fileInViewChanged({ fileId, inView: true }),
            ),
        state,
    );

const answerFor = async (search: SearchStateSlice) => {
    const tool = createGetTheseFilesTool(() => ({ search }) as RootState);
    return JSON.parse(await tool.handler({}));
};

describe("get_these_files", () => {
    it("answers with the loaded results, not just the visible ones", async () => {
        const answer = await answerFor(
            scrolledTo(withResults(10), ["f-3", "f-4"]),
        );

        expect(answer.success).toBe(true);
        expect(answer.file_ids).toHaveLength(10);
        expect(answer.file_ids[0]).toBe("f-0");
        expect(answer.visible_file_ids).toEqual(["f-3", "f-4"]);
    });

    // The list auto-loads as the user scrolls, so this is unbounded without a
    // cap. Report the truncation rather than quietly shortening the answer.
    it("caps a long list and says so", async () => {
        const answer = await answerFor(withResults(150, 4_000));

        expect(answer.file_ids).toHaveLength(100);
        expect(answer.truncated).toBe(true);
        expect(answer.loaded_count).toBe(150);
        expect(answer.total_files).toBe(4_000);
    });

    it("does not claim truncation for a list that fits", async () => {
        const answer = await answerFor(withResults(10));

        expect(answer.truncated).toBe(false);
        expect(answer.loaded_count).toBe(10);
    });

    it("reports the visible cards in rank order, not scroll order", async () => {
        const answer = await answerFor(
            scrolledTo(withResults(10), ["f-7", "f-5", "f-6"]),
        );

        expect(answer.visible_file_ids).toEqual(["f-5", "f-6", "f-7"]);
    });

    // Nothing is loaded, as opposed to nothing being scrolled into view: a
    // windowed list makes an empty viewport easy to hit, and that is not an
    // error.
    it("errors only when no results are loaded at all", async () => {
        expect((await answerFor(emptySearchState())).success).toBe(false);
        expect((await answerFor(withResults(3))).success).toBe(true);
    });
});
