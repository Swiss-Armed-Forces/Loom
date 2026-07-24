import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DemoUnavailableFeature } from "@features/common/utils/demoMode";

import { BurgerMenu } from "./BurgerMenu";

const dispatch = vi.hoisted(() => vi.fn());
const notifyIfUnavailableInDemoMode = vi.hoisted(() => vi.fn());

vi.mock("@app/hooks", () => ({
    useAppDispatch: () => dispatch,
}));

vi.mock("@features/common/demoModeUnavailableAction", () => ({
    notifyIfUnavailableInDemoMode,
}));

vi.mock("@mui/icons-material", () => {
    const Icon = () => <span aria-hidden="true" />;
    return {
        ApiOutlined: Icon,
        CloudCircleOutlined: Icon,
        CloudUploadOutlined: Icon,
        ExpandOutlined: Icon,
        FindInPageOutlined: Icon,
        InfoOutlined: Icon,
        InsightsOutlined: Icon,
        KeyOutlined: Icon,
        MailOutlineOutlined: Icon,
        Menu: Icon,
        PictureAsPdfOutlined: Icon,
        PrecisionManufacturingOutlined: Icon,
        QueueOutlined: Icon,
        SearchOutlined: Icon,
        SmartToyOutlined: Icon,
        StorageOutlined: Icon,
        TaskOutlined: Icon,
        WhatshotOutlined: Icon,
    };
});

vi.mock("@mui/material", () => ({
    IconButton: ({
        "aria-label": ariaLabel,
        children,
        onClick,
    }: React.ComponentProps<"button">) => (
        <button aria-label={ariaLabel} onClick={onClick}>
            {children}
        </button>
    ),
    Menu: ({ children, open }: React.PropsWithChildren<{ open: boolean }>) =>
        open ? <div role="menu">{children}</div> : null,
    MenuItem: ({
        children,
        component,
        ...props
    }: React.ComponentProps<"a"> & { component: "a" }) => {
        void component;
        return (
            <a role="menuitem" {...props}>
                {children}
            </a>
        );
    },
}));

vi.mock("react-i18next", () => ({
    useTranslation: () => ({
        t: (key: string) => (key === "about.title" ? "About" : key),
    }),
}));

const openMenu = () => {
    fireEvent.click(screen.getByRole("button", { name: "menu" }));
};

describe("BurgerMenu", () => {
    beforeEach(() => {
        dispatch.mockClear();
        notifyIfUnavailableInDemoMode.mockReset();
    });

    it("shows backend services and About", () => {
        render(<BurgerMenu />);

        openMenu();

        expect(
            screen.getByRole("menuitem", { name: "Open WebUI" }),
        ).toBeVisible();
        expect(screen.getByRole("menuitem", { name: "Traefik" })).toBeVisible();
        expect(screen.getByRole("menuitem", { name: "About" })).toBeVisible();
        expect(screen.getAllByRole("menuitem")).toHaveLength(18);
    });

    it("blocks unavailable demo service links and closes the menu", () => {
        notifyIfUnavailableInDemoMode.mockReturnValue(true);
        render(<BurgerMenu />);
        openMenu();
        const serviceLink = screen.getByRole("menuitem", {
            name: "Open WebUI",
        });
        const click = new MouseEvent("click", {
            bubbles: true,
            cancelable: true,
        });

        fireEvent(serviceLink, click);

        expect(notifyIfUnavailableInDemoMode).toHaveBeenCalledWith(
            DemoUnavailableFeature.BackendServices,
        );
        expect(click.defaultPrevented).toBe(true);
        expect(
            screen.queryByRole("menuitem", { name: "Open WebUI" }),
        ).not.toBeInTheDocument();
    });

    it("preserves production service link navigation", () => {
        notifyIfUnavailableInDemoMode.mockReturnValue(false);
        render(<BurgerMenu />);
        openMenu();
        const serviceLink = screen.getByRole("menuitem", { name: "Flower" });
        const click = new MouseEvent("click", {
            bubbles: true,
            cancelable: true,
        });

        fireEvent(serviceLink, click);

        expect(click.defaultPrevented).toBe(false);
        expect(serviceLink).toHaveAttribute("target", "_blank");
        expect(serviceLink).toHaveAttribute("rel", "noopener noreferrer");
    });
});
