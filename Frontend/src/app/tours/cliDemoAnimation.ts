const SHELL_PREFIX = "$ ";
const SHELL_CMD = "python cli.py";
const BANNER = "\n\nLoom archive shell.\nType 'help' for commands.\n\n";
const LAUNCH = SHELL_PREFIX + SHELL_CMD + BANNER;

const DEFAULT_PROMPT = "loom> ";

interface Step {
    cmd: string;
    output: string;
    promptAfter?: string;
}

const STEPS: Array<Step> = [
    {
        cmd: "ls",
        output: "  reports/annual.pdf\n  photos/field-ops.jpg",
    },
    {
        cmd: "cd reports/",
        output: "",
        promptAfter: "loom/reports> ",
    },
    {
        cmd: "cat annual.pdf",
        output:
            "  Jahresbericht 2024 \u2014 Dieser Bericht\n" +
            "  enth\u00e4lt vertrauliche Finanzdaten...",
    },
    {
        cmd: "translate annual.pdf en",
        output:
            "  Annual Report 2024 \u2014 This report\n" +
            "  contains confidential financial data...",
    },
    {
        cmd: "cd ..",
        output: "",
        promptAfter: DEFAULT_PROMPT,
    },
    {
        cmd: "tree",
        output:
            "  .\n" +
            "  \u251c\u2500\u2500 photos/\n" +
            "  \u2502   \u2514\u2500\u2500 field-ops.jpg\n" +
            "  \u2514\u2500\u2500 reports/\n" +
            "      \u2514\u2500\u2500 annual.pdf",
    },
];

const CURSOR = "\u258b";
const CHAR_MS = 52;
const AFTER_CMD_MS = 700;
const AFTER_OUTPUT_MS = 1_400;

export const startCliDemoAnimation = (el: HTMLElement): (() => void) => {
    let stopped = false;
    let tid: ReturnType<typeof setTimeout> | null = null;

    const later = (fn: () => void, ms: number) => {
        if (stopped) return;
        tid = setTimeout(() => {
            if (!stopped) fn();
        }, ms);
    };

    const setText = (text: string): void => {
        el.textContent = text;
        el.scrollTop = el.scrollHeight;
    };

    const typeCmd = (
        base: string,
        cmd: string,
        pos: number,
        prompt: string,
        onDone: () => void,
    ): void => {
        setText(base + prompt + cmd.slice(0, pos) + CURSOR);
        later(() => {
            if (pos >= cmd.length) {
                onDone();
            } else {
                typeCmd(base, cmd, pos + 1, prompt, onDone);
            }
        }, CHAR_MS);
    };

    const runStep = (base: string, stepIdx: number, prompt: string): void => {
        if (stepIdx >= STEPS.length) return;
        const { cmd, output, promptAfter } = STEPS[stepIdx];
        const nextPrompt = promptAfter ?? prompt;
        typeCmd(base, cmd, 0, prompt, () => {
            const afterTyping = base + prompt + cmd + "\n";
            later(() => {
                const withOutput =
                    output !== "" ? afterTyping + output + "\n" : afterTyping;
                // Show output and next prompt immediately, then wait before typing
                setText(withOutput + nextPrompt + CURSOR);
                later(
                    () => runStep(withOutput, stepIdx + 1, nextPrompt),
                    AFTER_OUTPUT_MS,
                );
            }, AFTER_CMD_MS);
        });
    };

    const typeLaunch = (pos: number): void => {
        setText(SHELL_PREFIX + SHELL_CMD.slice(0, pos) + CURSOR);
        later(() => {
            if (pos >= SHELL_CMD.length) {
                later(() => {
                    // Show banner and first prompt immediately, then wait before typing
                    setText(LAUNCH + DEFAULT_PROMPT + CURSOR);
                    later(
                        () => runStep(LAUNCH, 0, DEFAULT_PROMPT),
                        AFTER_OUTPUT_MS,
                    );
                }, AFTER_CMD_MS);
            } else {
                typeLaunch(pos + 1);
            }
        }, CHAR_MS);
    };

    setText(SHELL_PREFIX + CURSOR);
    later(() => typeLaunch(0), AFTER_OUTPUT_MS);

    return () => {
        stopped = true;
        if (tid !== null) {
            clearTimeout(tid);
            tid = null;
        }
    };
};
