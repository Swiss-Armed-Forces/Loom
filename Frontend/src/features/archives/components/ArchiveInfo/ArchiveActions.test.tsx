import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { ArchiveHit } from "@app/api";

import { ArchiveActions } from "./ArchiveActions";

const dispatch = vi.hoisted(() => vi.fn());

vi.mock("@app/hooks", () => ({ useAppDispatch: () => dispatch }));

vi.mock("react-i18next", () => ({
    useTranslation: () => ({ t: (key: string) => key }),
}));

const ARCHIVE = {
    fileId: "archive-1",
    sha256: "plain",
    sha256Encrypted: null,
    hidden: false,
} as unknown as ArchiveHit;

const LocationProbe = () => {
    const location = useLocation();
    return (
        <>
            <span data-testid="location-pathname">{location.pathname}</span>
            <span data-testid="location-search">{location.search}</span>
        </>
    );
};

describe("ArchiveActions", () => {
    it("asks for the archive's files through the URL alone", () => {
        render(
            <MemoryRouter initialEntries={["/archives"]}>
                <ArchiveActions archive={ARCHIVE} />
                <LocationProbe />
            </MemoryRouter>,
        );

        fireEvent.click(screen.getByTitle("tableView.actions.search"));

        expect(screen.getByTestId("location-pathname").textContent).toBe(
            "/search",
        );
        const params = new URLSearchParams(
            screen.getByTestId("location-search").textContent ?? "",
        );
        expect(params.get("query")).toBe('archives:"archive-1"');
        // A query handed to Redux beside the navigation is a second search
        // racing the one the search page runs for the URL.
        expect(dispatch).not.toHaveBeenCalled();
    });
});
