import { fireEvent, render, screen } from "@testing-library/react";
import { type ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DemoModeIndicator } from "./DemoModeIndicator";

const translations = vi.hoisted<Record<string, string>>(() => ({
    "about.link":
        "https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom",
    "common.close": "Close",
    "demoMode.indicator": "DEMO",
    "demoMode.introduction":
        "A browser-only preview of Loom using a curated set of sample documents. No backend needed.",
    "demoMode.limitations":
        "File uploads, imports, and backend services are unavailable. Changes reset on reload.",
    "demoMode.repository.action": "View on GitLab",
    "demoMode.startExploring": "Start exploring",
    "demoMode.title": "Interactive Demo",
    "demoMode.tour.description":
        "The guided tour covers search, results, sidebar tools, and more. It takes just a few minutes.",
    "demoMode.tour.title": "New here?",
    "tour.takeTour": "Take a Tour",
}));

vi.mock("@mui/icons-material", () => ({
    Close: () => <span aria-hidden="true">×</span>,
    InfoOutlined: () => <span aria-hidden="true">i</span>,
    RocketLaunch: () => <span aria-hidden="true">🚀</span>,
    ScienceOutlined: () => <span aria-hidden="true">S</span>,
    TourOutlined: () => <span aria-hidden="true">T</span>,
}));

vi.mock("@mui/material", () => ({
    Alert: ({ children }: { children: ReactNode }) => (
        <section>{children}</section>
    ),
    Box: ({ children }: { children: ReactNode }) => <div>{children}</div>,
    Button: ({
        children,
        onClick,
    }: {
        children: ReactNode;
        onClick?: () => void;
    }) => <button onClick={onClick}>{children}</button>,
    Dialog: ({
        children,
        id,
        onClose,
        open,
        "aria-labelledby": ariaLabelledBy,
    }: {
        children: ReactNode;
        id: string;
        onClose: () => void;
        open: boolean;
        "aria-labelledby": string;
    }) =>
        open ? (
            <div id={id} role="dialog" aria-labelledby={ariaLabelledBy}>
                {children}
                <button onClick={onClose}>Dismiss dialog</button>
            </div>
        ) : null,
    DialogActions: ({ children }: { children: ReactNode }) => (
        <div>{children}</div>
    ),
    DialogContent: ({ children }: { children: ReactNode }) => (
        <div>{children}</div>
    ),
    DialogTitle: ({ children }: { children: ReactNode }) => (
        <div>{children}</div>
    ),
    Divider: () => <hr />,
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
    Link: ({
        children,
        href,
        rel,
        target,
    }: {
        children: ReactNode;
        href: string;
        rel: string;
        target: string;
    }) => (
        <a href={href} rel={rel} target={target}>
            {children}
        </a>
    ),
    Stack: ({ children }: { children: ReactNode }) => <div>{children}</div>,
    Typography: ({
        children,
        component: Component = "p",
        id,
    }: {
        children: ReactNode;
        component?: "h3" | "p" | "span";
        id?: string;
    }) => <Component id={id}>{children}</Component>,
}));

vi.mock("react-i18next", () => ({
    useTranslation: () => ({
        t: (key: string) => translations[key] ?? key,
    }),
}));

vi.mock("react-router-dom", () => ({
    useLocation: () => ({ pathname: "/search" }),
    useNavigate: () => vi.fn(),
}));

vi.mock("@app/tours/useTour", () => ({
    useTour: () => ({ startTour: vi.fn() }),
}));

vi.mock("@app/tours/startWhenDialogsClose", () => ({
    startWhenDialogsClose: vi.fn(),
}));

describe("DemoModeIndicator", () => {
    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("opens automatically and shows all content", () => {
        render(<DemoModeIndicator />);
        const ribbon = screen.getByRole("button", { name: "DEMO" });

        expect(
            screen.getByRole("dialog", { name: "Interactive Demo" }),
        ).toBeVisible();
        expect(ribbon).toHaveAttribute("aria-expanded", "true");
        expect(
            screen.getByText(/A browser-only preview of Loom/),
        ).toBeInTheDocument();
        expect(screen.getByText(/File uploads, imports/)).toBeInTheDocument();
        expect(
            screen.getByRole("heading", { name: "New here?" }),
        ).toBeInTheDocument();

        const repositoryLink = screen.getByRole("link", {
            name: "View on GitLab",
        });
        expect(repositoryLink).toHaveAttribute(
            "href",
            "https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom",
        );
        expect(repositoryLink).toHaveAttribute("target", "_blank");
        expect(repositoryLink).toHaveAttribute("rel", "noopener noreferrer");
    });

    it("closes when 'Start exploring' is clicked and the ribbon can reopen it", () => {
        render(<DemoModeIndicator />);
        const ribbon = screen.getByRole("button", { name: "DEMO" });

        fireEvent.click(
            screen.getByRole("button", { name: "Start exploring" }),
        );

        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
        expect(ribbon).toHaveAttribute("aria-expanded", "false");

        fireEvent.click(ribbon);

        expect(
            screen.getByRole("dialog", { name: "Interactive Demo" }),
        ).toBeVisible();
        expect(ribbon).toHaveAttribute("aria-expanded", "true");
    });

    it("closes when the dialog onClose handler fires", () => {
        render(<DemoModeIndicator />);

        fireEvent.click(screen.getByRole("button", { name: "Dismiss dialog" }));

        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    it("closes when the X button is clicked", () => {
        render(<DemoModeIndicator />);

        fireEvent.click(screen.getByRole("button", { name: "Close" }));

        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
});
