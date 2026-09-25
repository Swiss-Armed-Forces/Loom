import { fireEvent, render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { setExpandFilePaths } from "@app/slices/searchSlice";
import { store } from "@app/store";

import { ClickableFilePath } from "./ClickableFilePath";

const DEEP_PATH = "/Crawler/Imports/archive.zip/testarchive/testfile01.txt";
const SHALLOW_PATH = "/Mail/Inbox/basic_email.eml";

const renderPath = (fullPath: string) =>
    render(
        <Provider store={store}>
            <ClickableFilePath fullPath={fullPath} />
        </Provider>,
    );

const trail = () => screen.getByRole("list").textContent;
// The breadcrumb segments render as links, so the toggle is the only button
// inside the trail.
const toggle = () => screen.getByRole("button");

describe("ClickableFilePath", () => {
    beforeEach(() => {
        store.dispatch(setExpandFilePaths(false));
    });

    it("heads the trail with the toggle, ahead of the visible tail", () => {
        renderPath(DEEP_PATH);

        // The toggle sits inside the trail with a separator after it - that
        // is what signals the path continues to the left.
        expect(trail()).toBe("/archive.zip/testarchive/testfile01.txt");
        expect(toggle()).toBeInTheDocument();
    });

    it("shows the whole path once expanded", () => {
        store.dispatch(setExpandFilePaths(true));
        renderPath(DEEP_PATH);

        expect(trail()).toBe(
            "/Crawler/Imports/archive.zip/testarchive/testfile01.txt",
        );
    });

    it("keeps the toggle heading the trail in both states", () => {
        const headsTheTrail = () =>
            screen.getByRole("list").firstChild?.contains(toggle());

        renderPath(DEEP_PATH);
        expect(headsTheTrail()).toBe(true);

        fireEvent.click(toggle());

        // Toggling swaps the icon but never moves the control, so the row
        // does not reflow under the pointer.
        expect(trail()).toContain("Crawler");
        expect(headsTheTrail()).toBe(true);
    });

    it("leaves short paths untouched, with no toggle at all", () => {
        renderPath(SHALLOW_PATH);

        expect(trail()).toBe("Mail/Inbox/basic_email.eml");
        expect(screen.queryByRole("button")).toBeNull();
    });

    it("expands every card from one click, not just its own", () => {
        renderPath(DEEP_PATH);
        fireEvent.click(toggle());

        expect(store.getState().search.expandFilePaths).toBe(true);
    });

    it("reaches no ancestor handler, by click or by focus", () => {
        // The result card highlights itself from both events, and a highlight
        // mid-click re-renders the row and swallows the click.
        const onClick = vi.fn();
        const onFocus = vi.fn();

        render(
            <div onClick={onClick} onFocus={onFocus}>
                <Provider store={store}>
                    <ClickableFilePath fullPath={DEEP_PATH} />
                </Provider>
            </div>,
        );

        fireEvent.focus(toggle());
        fireEvent.click(toggle());

        expect(onFocus).not.toHaveBeenCalled();
        expect(onClick).not.toHaveBeenCalled();
        expect(store.getState().search.expandFilePaths).toBe(true);
    });
});
