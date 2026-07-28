import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useTour } from "@app/tours/useTour";

import { SearchResults } from "./SearchResults";

vi.mock("@app/tours/useTour", () => ({
    useTour: vi.fn(),
}));

vi.mock("@features/search/components", () => ({
    // eslint-disable-next-line react/prop-types
    EmptySearchResults: ({ forceQueryOverview = false }) => (
        <div data-testid="query-overview" data-forced={forceQueryOverview} />
    ),
}));

vi.mock("./Detailed/DetailedView", () => ({
    DetailedView: () => <div data-testid="detailed-results" />,
}));

const mockedUseTour = vi.mocked(useTour);

const tourContext = (opts: {
    showQueryOverview: boolean;
    isTourActive?: boolean;
}) => ({
    dismissActiveTour: vi.fn(),
    isTourActive: opts.isTourActive ?? opts.showQueryOverview,
    showQueryOverview: opts.showQueryOverview,
    activeTourStepId: null,
    tourDetailFileId: null,
    startTour: vi.fn(),
});

describe("SearchResults", () => {
    beforeEach(() => vi.clearAllMocks());

    it("shows the normal detailed results outside a tour", () => {
        mockedUseTour.mockReturnValue(
            tourContext({ showQueryOverview: false }),
        );

        render(<SearchResults />);

        expect(screen.getByTestId("detailed-results")).toBeInTheDocument();
        expect(screen.queryByTestId("query-overview")).toBeNull();
    });

    it("forces the query overview while a tour is active", () => {
        mockedUseTour.mockReturnValue(tourContext({ showQueryOverview: true }));

        render(<SearchResults />);

        expect(screen.getByTestId("query-overview")).toHaveAttribute(
            "data-forced",
            "true",
        );
        expect(screen.queryByTestId("detailed-results")).toBeNull();
    });

    it("shows real results during the final tour step", () => {
        mockedUseTour.mockReturnValue(
            tourContext({ showQueryOverview: false, isTourActive: true }),
        );

        render(<SearchResults />);

        expect(screen.getByTestId("detailed-results")).toBeInTheDocument();
        expect(screen.queryByTestId("query-overview")).toBeNull();
    });
});
