/**
 * Controls that own their click, and must therefore never also trigger the
 * action of the card they sit in.
 *
 * A result card turns a click or a focus on its body into "highlight me", and
 * a Ctrl-click into "open my file in a background tab". Every interactive
 * child of the card bubbles its own events through that handler, so without a
 * guard a Ctrl-click on one attachment chip opens a tab for the attachment
 * *and* a tab for the mail carrying it.
 *
 * MUI renders every button-like component through ButtonBase, which marks a
 * non-`<button>` root with `role="button"` — a clickable `Chip` included. The
 * roles below therefore cover the MUI components without naming any of their
 * classes, and they leave the decorative chips (no handler, no role) matching
 * nothing, so clicking those still highlights the card.
 */
const INTERACTIVE_SELECTOR =
    "button, a, [role='button'], [role='menuitem'], [role='tab']";

/**
 * True when the event originates from an interactive control inside the card
 * rather than from the card body itself.
 */
export const isInteractiveTarget = (target: EventTarget | null): boolean =>
    target instanceof Element && target.closest(INTERACTIVE_SELECTOR) !== null;
