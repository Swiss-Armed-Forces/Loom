import { fireEvent, render, screen } from "@testing-library/react";
import { SyntheticEvent } from "react";
import { Provider } from "react-redux";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Attachment } from "@app/api";
import { closeFileTab, setActiveTabFileId } from "@app/slices/searchSlice";
import { store } from "@app/store";
import { FileDetailTab } from "@features/common/utils/enums";

import { isInteractiveTarget } from "../interactiveTarget";

import { FileAttachments } from "./FileAttachments";

const ATTACHMENTS: Attachment[] = [
    { id: "attachment-1", name: "first.txt" },
    { id: "attachment-2", name: "second.pdf" },
];

// The component measures its chips to decide whether to collapse them; jsdom
// has no ResizeObserver, and every measured width is 0, so the chips stay
// expanded and the popover is reached through the keyboard shortcut's button.
class ResizeObserverStub {
    observe = vi.fn();
    unobserve = vi.fn();
    disconnect = vi.fn();
}
vi.stubGlobal("ResizeObserver", ResizeObserverStub);

const openTabs = () => store.getState().search.openFileTabs;
const activeTab = () => store.getState().search.activeTabFileId;

/**
 * Renders the attachments the way a result card holds them: inside an element
 * that runs the card's own click and focus action, gated by the card's guard.
 * The guard is imported rather than restated, so the test fails if the card
 * stops recognising an attachment control as interactive.
 */
const renderInCard = () => {
    const cardAction = vi.fn();
    const handleCardEvent = (event: SyntheticEvent) => {
        if (!isInteractiveTarget(event.target)) {
            cardAction(event.type);
        }
    };

    render(
        <div
            data-testid="card"
            tabIndex={0}
            onClick={handleCardEvent}
            onFocus={handleCardEvent}
        >
            <Provider store={store}>
                <FileAttachments attachments={ATTACHMENTS} />
            </Provider>
        </div>,
    );

    return cardAction;
};

describe("FileAttachments", () => {
    beforeEach(() => {
        for (const tab of [...openTabs()]) {
            store.dispatch(closeFileTab(tab.fileId));
        }
        store.dispatch(setActiveTabFileId(null));
    });

    it("opens only the attachment on Ctrl-click, not the card's file", () => {
        const cardAction = renderInCard();

        fireEvent.click(screen.getByRole("button", { name: "second.pdf" }), {
            ctrlKey: true,
        });

        // Exactly one tab, for the attachment, in the background - the card's
        // own file must not be dragged along.
        expect(openTabs()).toEqual([
            { fileId: "attachment-2", detailTab: FileDetailTab.Rendered },
        ]);
        expect(activeTab()).toBeNull();
        expect(cardAction).not.toHaveBeenCalled();
    });

    it("opens only the attachment on a plain click", () => {
        const cardAction = renderInCard();

        fireEvent.click(screen.getByRole("button", { name: "first.txt" }));

        expect(openTabs()).toEqual([
            { fileId: "attachment-1", detailTab: FileDetailTab.Rendered },
        ]);
        expect(activeTab()).toBe("attachment-1");
        expect(cardAction).not.toHaveBeenCalled();
    });

    it("opens only the attachment from a popover entry", () => {
        const cardAction = renderInCard();

        // The `c` shortcut opens the popover through this hidden button.
        fireEvent.click(screen.getByLabelText("show-attachments"));

        fireEvent.click(screen.getByRole("menuitem", { name: "second.pdf" }), {
            ctrlKey: true,
        });

        expect(openTabs()).toEqual([
            { fileId: "attachment-2", detailTab: FileDetailTab.Rendered },
        ]);
        expect(activeTab()).toBeNull();
        expect(cardAction).not.toHaveBeenCalled();
    });

    it("leaves the card's highlight-on-focus intact", () => {
        const cardAction = renderInCard();

        fireEvent.focus(screen.getByTestId("card"));

        expect(cardAction).toHaveBeenCalledWith("focus");

        cardAction.mockClear();

        // Focus on a chip belongs to the chip. Letting it through would
        // highlight the card and re-render it between mousedown and mouseup,
        // swallowing the very click the focus came with.
        fireEvent.focus(screen.getByRole("button", { name: "second.pdf" }));

        expect(cardAction).not.toHaveBeenCalled();
    });
});
