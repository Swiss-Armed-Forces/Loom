import { render, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { StatisticsView } from "./StatisticsView";

const apiMocks = vi.hoisted(() => ({
    getHistogramStat: vi.fn(),
    getHistogramStats: vi.fn(),
    getTermsStat: vi.fn(),
    getTermsStats: vi.fn(),
}));
const dispatch = vi.hoisted(() => vi.fn());
const searchState = vi.hoisted(() => ({
    displayHistogramStat: "size",
    displayStat: "extension",
    histogramStats: [{ id: "size", label: "Size" }],
    query: {
        id: "query-id",
        keepAlive: "30m",
        pageSize: null,
        query: "*",
        sortDirection: null,
        sortField: null,
        sortId: null,
    },
    stats: { histogramData: null, termsData: null },
    termsStats: [{ id: "extension", label: "Extension" }],
}));

vi.mock("@app/api", () => apiMocks);
vi.mock("@app/hooks", () => ({
    useAppSelector: (selector: (state: unknown) => unknown) =>
        selector({ search: searchState }),
}));
vi.mock("react-redux", () => ({ useDispatch: () => dispatch }));
vi.mock("react-i18next", () => ({
    useTranslation: () => ({ t: (key: string) => key }),
}));
vi.mock("@mui/icons-material", () => ({
    BarChart: () => null,
    Description: () => null,
    VerticalAlignBottom: () => null,
    VerticalAlignTop: () => null,
}));
vi.mock("@mui/material", () => ({
    Divider: () => null,
    FormControl: ({ children }: { children: ReactNode }) => children,
    InputLabel: ({ children }: { children: ReactNode }) => children,
    MenuItem: ({ children }: { children: ReactNode }) => children,
    Select: ({ children }: { children: ReactNode }) => children,
    Typography: ({ children }: { children: ReactNode }) => children,
}));
vi.mock("@features/search/components", () => ({
    Chart: () => null,
    HistogramChart: () => null,
    computeOthersCount: () => 0,
}));

describe("StatisticsView", () => {
    afterEach(() => {
        vi.clearAllMocks();
    });

    it("refreshes statistics when the view first opens", async () => {
        apiMocks.getTermsStat.mockResolvedValue({
            data: [],
            fileCount: 0,
            key: "extension",
            stat: "extension",
        });
        apiMocks.getHistogramStat.mockResolvedValue({
            data: [],
            fileCount: 0,
            groupBy: "extension",
            histogramType: "number",
            key: "size",
            stat: "size",
        });

        const view = render(<StatisticsView />);

        await waitFor(() => {
            expect(apiMocks.getTermsStat).toHaveBeenCalledWith(
                expect.objectContaining({ id: null, query: "*" }),
                "extension",
                5,
                expect.any(AbortSignal),
            );
            expect(apiMocks.getHistogramStat).toHaveBeenCalledWith(
                expect.objectContaining({ id: null, query: "*" }),
                "size",
                "extension",
                expect.any(AbortSignal),
            );
        });

        const signal = apiMocks.getTermsStat.mock.calls[0][3] as AbortSignal;
        expect(signal.aborted).toBe(false);
        view.unmount();
        expect(signal.aborted).toBe(true);
    });
});
