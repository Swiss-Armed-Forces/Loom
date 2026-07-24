import { describe, expect, it } from "vitest";

import {
    buildApiBasePath,
    buildWebSocketApiBasePath,
} from "./apiConfiguration";

describe("API base path configuration", () => {
    it("uses the root API path for the ordinary frontend", () => {
        expect(buildApiBasePath("https://frontend.loom", "/")).toBe(
            "https://frontend.loom/api",
        );
        expect(buildWebSocketApiBasePath("https://frontend.loom", "/")).toBe(
            "wss://frontend.loom/api",
        );
    });

    it("keeps API requests inside a Pages subpath", () => {
        expect(buildApiBasePath("https://example.gitlab.io", "/loom/")).toBe(
            "https://example.gitlab.io/loom/api",
        );
        expect(
            buildWebSocketApiBasePath("https://example.gitlab.io", "/loom/"),
        ).toBe("wss://example.gitlab.io/loom/api");
    });

    it("uses an insecure WebSocket only for an HTTP origin", () => {
        expect(
            buildWebSocketApiBasePath("http://localhost:4173", "/loom"),
        ).toBe("ws://localhost:4173/loom/api");
    });
});
