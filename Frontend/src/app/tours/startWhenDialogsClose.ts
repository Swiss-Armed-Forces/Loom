const DIALOG_POLL_INTERVAL_MS = 250;

export const startWhenDialogsClose = (start: () => void): (() => void) => {
    let timeout: ReturnType<typeof setTimeout>;
    let cancelled = false;

    const tryStart = () => {
        if (cancelled) return;
        if (document.querySelector('[role="dialog"]')) {
            timeout = setTimeout(tryStart, DIALOG_POLL_INTERVAL_MS);
            return;
        }
        start();
    };

    timeout = setTimeout(tryStart, 0);
    return () => {
        cancelled = true;
        clearTimeout(timeout);
    };
};
