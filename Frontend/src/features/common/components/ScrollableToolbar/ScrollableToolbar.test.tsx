import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ScrollableToolbar } from "./ScrollableToolbar";

// jsdom has no layout engine, so the row measures zero in every direction and
// implements no scrolling at all. Both have to be stated for the component to
// have anything to react to.
const renderToolbar = (scrollWidth: number, clientWidth: number) => {
    render(
        <ScrollableToolbar>
            <button>one</button>
            <button>two</button>
        </ScrollableToolbar>,
    );
    const row = screen.getByTestId("toolbar-scroll-row");
    Object.defineProperty(row, "scrollWidth", {
        configurable: true,
        value: scrollWidth,
    });
    Object.defineProperty(row, "clientWidth", {
        configurable: true,
        value: clientWidth,
    });
    row.scrollBy = vi.fn();
    fireEvent.scroll(row);
    return row;
};

describe("ScrollableToolbar", () => {
    it("shows no arrows while the content fits", () => {
        renderToolbar(300, 300);

        expect(screen.queryByTestId("toolbar-scroll-start")).toBeNull();
        expect(screen.queryByTestId("toolbar-scroll-end")).toBeNull();
    });

    it("offers only the forward arrow at the start of an overflowing row", () => {
        renderToolbar(500, 300);

        expect(screen.getByTestId("toolbar-scroll-start")).toHaveClass(
            "Mui-disabled",
        );
        expect(screen.getByTestId("toolbar-scroll-end")).not.toHaveClass(
            "Mui-disabled",
        );
    });

    it("offers only the back arrow once the row is scrolled to its end", () => {
        const row = renderToolbar(500, 300);
        row.scrollLeft = 200;
        fireEvent.scroll(row);

        expect(screen.getByTestId("toolbar-scroll-start")).not.toHaveClass(
            "Mui-disabled",
        );
        expect(screen.getByTestId("toolbar-scroll-end")).toHaveClass(
            "Mui-disabled",
        );
    });

    it("scrolls by a visible row's width per click", () => {
        const row = renderToolbar(500, 300);

        fireEvent.click(screen.getByTestId("toolbar-scroll-end"));

        expect(row.scrollBy).toHaveBeenCalledWith({
            left: 300,
            behavior: "smooth",
        });
    });
});
