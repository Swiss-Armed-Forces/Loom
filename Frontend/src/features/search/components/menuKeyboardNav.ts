import React from "react";

/**
 * onKeyDown handler for MUI <Menu> components that adds vim-style j/k navigation
 * on top of MUI's built-in arrow-key navigation, and prevents global hotkeys
 * from firing while the menu is open.
 *
 * Calling e.preventDefault() sets defaultPrevented on the native event, which
 * causes shouldIgnoreKeyEvent in useKeyboardNavigation to skip the event — so
 * global j/k card-navigation and the global ESC handler are suppressed while a
 * menu is open.
 */
export const menuJKNavigation = (e: React.KeyboardEvent): void => {
    if (e.key === "Escape") {
        // Prevent the global ESC handler from also firing (e.g. unhighlighting
        // a card) when the user just wants to close this menu.
        e.preventDefault();
        return;
    }
    if (e.key !== "j" && e.key !== "k") return;
    e.preventDefault();
    const items = Array.from(
        e.currentTarget.querySelectorAll<HTMLElement>(
            '[role="menuitem"]:not([aria-disabled="true"])',
        ),
    );
    if (!items.length) return;
    const currentIdx = items.indexOf(document.activeElement as HTMLElement);
    if (e.key === "j") {
        items[
            currentIdx === -1 ? 0 : Math.min(currentIdx + 1, items.length - 1)
        ]?.focus();
    } else {
        items[
            currentIdx === -1 ? items.length - 1 : Math.max(currentIdx - 1, 0)
        ]?.focus();
    }
};
