import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";
import "@testing-library/jest-dom";

// runs a cleanup after each test case
afterEach(() => {
    cleanup();
});

// jsdom implements neither observer, and anything rendering the result list
// reaches for both: the virtualizer measures rows with a ResizeObserver, and
// result cards track visibility with an IntersectionObserver. Both stubs are
// inert — a test that needs elements to report a size has to say so itself,
// since jsdom has no layout engine and measures everything as zero.
class InertObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
    takeRecords() {
        return [];
    }
}

vi.stubGlobal("ResizeObserver", InertObserver);
vi.stubGlobal(
    "IntersectionObserver",
    class extends InertObserver {
        readonly root = null;
        readonly rootMargin = "";
        readonly thresholds: number[] = [];
    },
);

Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
    })),
});

// jsdom implements no element scrolling at all, so `el.scrollTo` is not a
// function rather than a no-op. Code that scrolls a panel into place would
// throw instead of doing nothing.
Element.prototype.scrollTo = vi.fn();
