import { fireEvent, render, screen } from "@testing-library/react";
import { type ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { DemoModeIndicator } from "./DemoModeIndicator";

const translations = vi.hoisted<Record<string, string>>(() => ({
    "common.close": "Close",
    "demoMode.description":
        "No Loom backend services are connected. Actions use sample data and are simulated locally in your browser. Changes are temporary and reset when you reload the page.",
    "demoMode.indicator": "DEMO",
    "demoMode.title": "Demo mode",
}));

vi.mock("@mui/icons-material", () => ({
    Close: () => <span aria-hidden="true">×</span>,
}));

vi.mock("@mui/material", () => ({
    Dialog: ({
        children,
        id,
        open,
        "aria-labelledby": ariaLabelledBy,
    }: {
        children: ReactNode;
        id: string;
        open: boolean;
        "aria-labelledby": string;
    }) =>
        open ? (
            <div id={id} role="dialog" aria-labelledby={ariaLabelledBy}>
                {children}
            </div>
        ) : null,
    DialogContent: ({ children }: { children: ReactNode }) => (
        <div>{children}</div>
    ),
    DialogTitle: ({ children, id }: { children: ReactNode; id: string }) => (
        <h2 id={id}>{children}</h2>
    ),
    IconButton: ({
        "aria-label": ariaLabel,
        children,
        onClick,
        title,
    }: {
        "aria-label": string;
        children: ReactNode;
        onClick: () => void;
        title: string;
    }) => (
        <button aria-label={ariaLabel} title={title} onClick={onClick}>
            {children}
        </button>
    ),
    Typography: ({ children }: { children: ReactNode }) => <p>{children}</p>,
}));

vi.mock("react-i18next", () => ({
    useTranslation: () => ({
        t: (key: string) => translations[key] ?? key,
    }),
}));

describe("DemoModeIndicator", () => {
    it("renders the demo ribbon in its closed state", () => {
        render(<DemoModeIndicator />);

        const ribbon = screen.getByRole("button", { name: "DEMO" });
        expect(ribbon).toHaveAttribute("aria-expanded", "false");
    });

    it("opens, closes, and reopens the demo explanation", () => {
        render(<DemoModeIndicator />);

        const ribbon = screen.getByRole("button", { name: "DEMO" });

        fireEvent.click(ribbon);

        expect(
            screen.getByRole("dialog", { name: "Demo mode" }),
        ).toBeInTheDocument();
        expect(
            screen.getByText(/No Loom backend services are connected/),
        ).toBeInTheDocument();
        expect(ribbon).toHaveAttribute("aria-expanded", "true");

        fireEvent.click(screen.getByRole("button", { name: "Close" }));

        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
        expect(ribbon).toHaveAttribute("aria-expanded", "false");

        fireEvent.click(ribbon);

        expect(
            screen.getByRole("dialog", { name: "Demo mode" }),
        ).toBeInTheDocument();
    });
});
