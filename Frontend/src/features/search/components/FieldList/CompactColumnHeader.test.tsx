import { fireEvent, render } from "@testing-library/react";
import { Provider } from "react-redux";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
    addFieldColumn,
    removeFieldColumn,
    selectCompactColumnWidths,
    setCompactColumnWidths,
    setPreviewFields,
} from "@app/slices/searchSlice";
import { store } from "@app/store";

import { CompactColumnHeader } from "./CompactColumnHeader";

vi.mock("react-i18next", () => ({
    useTranslation: () => ({ t: (key: string) => key }),
}));

const renderHeader = () =>
    render(
        <Provider store={store}>
            <CompactColumnHeader />
        </Provider>,
    );

const handles = (container: HTMLElement) =>
    container.querySelectorAll<HTMLElement>('[role="separator"]');

describe("CompactColumnHeader", () => {
    afterEach(() => {
        store.dispatch(setPreviewFields(["content"]));
        store.dispatch(setCompactColumnWidths([]));
        store.dispatch(removeFieldColumn());
        store.dispatch(removeFieldColumn());
    });

    it("counts the card's columns rather than its fields", () => {
        store.dispatch(setPreviewFields(["content"]));
        store.dispatch(addFieldColumn());
        store.dispatch(addFieldColumn());

        const { container } = renderHeader();

        // One field selected, three columns, and the cells are the columns:
        // three of them have two borders between, the outer edges being the
        // list's own padding.
        expect(handles(container)).toHaveLength(2);
    });

    it("evens out the pair a border separates when it is double-clicked", () => {
        store.dispatch(addFieldColumn());
        store.dispatch(addFieldColumn());
        store.dispatch(setCompactColumnWidths([2, 0.5, 1]));

        const { container } = renderHeader();
        fireEvent.doubleClick(handles(container)[0]);

        // Only the pair moves and their sum is kept, so the third column
        // stays where it was and the row still fits.
        expect(selectCompactColumnWidths(store.getState())).toEqual([
            1.25, 1.25, 1,
        ]);
    });
});
