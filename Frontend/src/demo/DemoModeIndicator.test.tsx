import { fireEvent, render, screen } from "@testing-library/react";
import { type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

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
        "Search with Loom's query syntax, then explore folders, statistics, metadata, previews, and downloads.",
    "demoMode.capabilities.title": "What you can explore",
    "demoMode.indicator": "DEMO",
    "demoMode.introduction":
        "This is a browser-only preview of Loom. It uses a curated set of sample documents and simulates Loom's APIs, background tasks, and live updates, so you can explore the interface without deploying the full stack.",
    "demoMode.limitations.backend":
        "No Loom backend services are connected. File uploads, archive imports, service dashboards, and task-execution details are unavailable.",
    "demoMode.limitations.reset":
        "Changes to demo data and generated results are temporary and reset when you reload the page.",
    "demoMode.limitations.title": "Demo boundaries",
    "demoMode.repository.prompt":
        "Want to run Loom with your own documents? Visit the project repository for installation instructions and more information.",
    "demoMode.startExploring": "Start exploring",
    "demoMode.title": "Demo mode",
}));

const DEMO_INTRODUCTION_SEEN_KEY = "loom:demo-introduction-seen:v1";

vi.mock("@mui/icons-material", () => ({
    CheckCircleOutlined: () => <span aria-hidden="true">✓</span>,
    Close: () => <span aria-hidden="true">×</span>,
    InfoOutlined: () => <span aria-hidden="true">i</span>,
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
    beforeEach(() => {
        window.localStorage.clear();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("opens automatically on the first visit and persists dismissal", () => {
        const { unmount } = render(<DemoModeIndicator />);
        const ribbon = screen.getByRole("button", { name: "DEMO" });

        expect(screen.getByRole("dialog", { name: "Demo mode" })).toBeVisible();
        expect(ribbon).toHaveAttribute("aria-expanded", "true");
        expect(
            screen.getByText(/This is a browser-only preview of Loom/),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("heading", { name: "What you can explore" }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("heading", { name: "Demo boundaries" }),
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

        fireEvent.click(
            screen.getByRole("button", { name: "Start exploring" }),
        );

        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
        expect(ribbon).toHaveAttribute("aria-expanded", "false");
        expect(window.localStorage.getItem(DEMO_INTRODUCTION_SEEN_KEY)).toBe(
            "true",
        );

        unmount();
        render(<DemoModeIndicator />);

        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    it("keeps the dialog closed for returning visitors and allows manual replay", () => {
        window.localStorage.setItem(DEMO_INTRODUCTION_SEEN_KEY, "true");
        render(<DemoModeIndicator />);

        const ribbon = screen.getByRole("button", { name: "DEMO" });
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
        expect(ribbon).toHaveAttribute("aria-expanded", "false");

        fireEvent.click(ribbon);

        expect(screen.getByRole("dialog", { name: "Demo mode" })).toBeVisible();
        expect(ribbon).toHaveAttribute("aria-expanded", "true");
    });

    it("persists dismissal from the dialog onClose handler", () => {
        render(<DemoModeIndicator />);

        fireEvent.click(screen.getByRole("button", { name: "Dismiss dialog" }));

        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
        expect(window.localStorage.getItem(DEMO_INTRODUCTION_SEEN_KEY)).toBe(
            "true",
        );
    });

    it("remains usable when localStorage is unavailable", () => {
        vi.spyOn(Storage.prototype, "getItem").mockImplementationOnce(() => {
            throw new DOMException("Storage is blocked");
        });
        vi.spyOn(Storage.prototype, "setItem").mockImplementationOnce(() => {
            throw new DOMException("Storage is blocked");
        });
        vi.spyOn(console, "warn").mockImplementation(() => undefined);
        render(<DemoModeIndicator />);

        expect(screen.getByRole("dialog", { name: "Demo mode" })).toBeVisible();

        fireEvent.click(screen.getByRole("button", { name: "Close" }));

        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
        expect(console.warn).toHaveBeenCalledWith(
            "Unable to persist the demo introduction state.",
            expect.any(DOMException),
        );
    });
});
