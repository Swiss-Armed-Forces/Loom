import { fireEvent, render, screen } from "@testing-library/react";
import { type ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DemoModeIndicator } from "./DemoModeIndicator";

const translations = vi.hoisted<Record<string, string>>(() => ({
    "about.link":
        "https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom",
    "common.close": "Close",
    "demoMode.capabilities.automation":
        "Try simulated summarization, translation, image descriptions, reindexing, and document chat.",
    "demoMode.capabilities.organize":
        "Tag, flag, hide, and mark documents as seen, or create and download demo archives.",
    "demoMode.capabilities.search":
        "Search with Loom's query syntax and explore folders, statistics, metadata, previews, and downloads.",
    "demoMode.capabilities.title": "What's available",
    "demoMode.indicator": "DEMO",
    "demoMode.introduction":
        "This is a browser-only preview of Loom using a curated set of sample documents. No backend is required — everything runs in your browser.",
    "demoMode.limitations.backend":
        "File uploads, archive imports, service dashboards, and task details are unavailable.",
    "demoMode.limitations.reset": "Changes reset on page reload.",
    "demoMode.limitations.title": "Limitations",
    "demoMode.repository.prompt": "Want to run Loom with your own documents?",
    "demoMode.startExploring": "Start exploring",
    "demoMode.title": "Interactive Demo",
}));

vi.mock("@mui/icons-material", () => ({
    CheckCircleOutlined: () => <span aria-hidden="true">✓</span>,
    Close: () => <span aria-hidden="true">×</span>,
    InfoOutlined: () => <span aria-hidden="true">i</span>,
    RocketLaunch: () => <span aria-hidden="true">🚀</span>,
    ScienceOutlined: () => <span aria-hidden="true">S</span>,
}));

vi.mock("@mui/material", () => ({
    Alert: ({ children }: { children: ReactNode }) => (
        <section>{children}</section>
    ),
    AlertTitle: ({ children }: { children: ReactNode }) => <h3>{children}</h3>,
    Box: ({ children }: { children: ReactNode }) => <div>{children}</div>,
    Button: ({
        children,
        onClick,
    }: {
        children: ReactNode;
        onClick?: () => void;
    }) => <button onClick={onClick}>{children}</button>,
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
    DialogContent: ({ children }: { children: ReactNode }) => (
        <div>{children}</div>
    ),
    DialogActions: ({ children }: { children: ReactNode }) => (
        <div>{children}</div>
    ),
    DialogTitle: ({ children }: { children: ReactNode }) => (
        <div>{children}</div>
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
    List: ({ children }: { children: ReactNode }) => <ul>{children}</ul>,
    ListItem: ({ children }: { children: ReactNode }) => <li>{children}</li>,
    ListItemIcon: ({ children }: { children: ReactNode }) => (
        <span>{children}</span>
    ),
    ListItemText: ({ primary }: { primary: ReactNode }) => (
        <span>{primary}</span>
    ),
    Paper: ({ children }: { children: ReactNode }) => (
        <section>{children}</section>
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
            screen.getByText(/This is a browser-only preview of Loom/),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("heading", { name: "What's available" }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("heading", { name: "Limitations" }),
        ).toBeInTheDocument();
        expect(
            screen.getByText(/File uploads, archive imports/),
        ).toBeInTheDocument();

        const repositoryLink = screen.getByRole("link", {
            name: "https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom",
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
