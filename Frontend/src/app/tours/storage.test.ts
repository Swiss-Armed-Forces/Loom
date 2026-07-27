import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { loadTourState, saveTourState, TOUR_STORAGE_KEY } from "./storage";

describe("tour storage", () => {
    beforeEach(() => window.localStorage.clear());
    afterEach(() => vi.restoreAllMocks());

    it("round-trips valid state", () => {
        const state = {
            schemaVersion: 1 as const,
            outcome: "completed" as const,
        };

        saveTourState(state);

        expect(loadTourState()).toEqual(state);
    });

    it.each([
        "not json",
        '{"schemaVersion":2}',
        '{"schemaVersion":1,"outcome":"unknown"}',
    ])("recovers from invalid state: %s", (stored) => {
        window.localStorage.setItem(TOUR_STORAGE_KEY, stored);
        expect(loadTourState()).toEqual({ schemaVersion: 1 });
    });

    it("continues when localStorage is unavailable", () => {
        vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
            throw new DOMException("blocked");
        });
        expect(loadTourState()).toEqual({ schemaVersion: 1 });

        vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
            throw new DOMException("blocked");
        });
        expect(() => saveTourState({ schemaVersion: 1 })).not.toThrow();
    });
});
