import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { FieldRow } from "./FieldRow";

vi.mock("react-i18next", () => ({
    useTranslation: () => ({ t: (key: string) => key }),
}));

const FROM = "alice@example.org";

describe("FieldRow", () => {
    it("renders the field as a single label: value line", () => {
        const { container } = render(<FieldRow field="from" value={FROM} />);

        expect(container.textContent).toBe(`from:${FROM}`);
    });

    it("spends no accordion and no divider on a short value", () => {
        // The accordion and its top border are exactly the chrome this layout
        // exists to drop - five fields used to cost five of each per card.
        const { container } = render(<FieldRow field="from" value={FROM} />);

        expect(container.querySelector(".MuiAccordion-root")).toBeNull();
        expect(container.querySelector(".MuiChip-root")).toBeNull();
        expect(screen.queryByRole("button")).toBeNull();
    });

    it("marks search hits as <em>, as the rows layout does", () => {
        const { container } = render(
            <FieldRow
                field="subject"
                value="Re: <highlight>invoice</highlight> attached"
            />,
        );

        const marks = container.querySelectorAll("em");
        expect(marks).toHaveLength(1);
        expect(marks[0]).toHaveTextContent("invoice");
        // The markers themselves never reach the reader, in the value or in
        // the title that carries the untruncated text.
        expect(container.textContent).not.toContain("<highlight>");
        expect(container.querySelector("[title]")?.getAttribute("title")).toBe(
            "Re: invoice attached",
        );
    });

    it("keeps the actions mounted so focus can reach them", () => {
        // They are revealed by opacity on hover/focus - unmounting them, or
        // hiding them with display/visibility, would take them off the tab
        // order and shift the row when they came back.
        const onQuery = vi.fn();
        const onSort = vi.fn();

        render(
            <FieldRow
                field="from"
                value={FROM}
                onQuery={onQuery}
                onSort={onSort}
            />,
        );

        const buttons = screen.getAllByRole("button");
        expect(buttons).toHaveLength(2);
        for (const button of buttons) {
            button.focus();
            expect(button).toHaveFocus();
        }
    });

    it("keeps a click on the actions off the surrounding card", () => {
        // The result card highlights itself on click, which re-renders the row
        // and would swallow the action.
        const onCardClick = vi.fn();
        const onQuery = vi.fn();

        render(
            <div onClick={onCardClick}>
                <FieldRow field="from" value={FROM} onQuery={onQuery} />
            </div>,
        );

        fireEvent.click(screen.getByRole("button"));

        expect(onQuery).toHaveBeenCalledTimes(1);
        expect(onCardClick).not.toHaveBeenCalled();
    });
});
