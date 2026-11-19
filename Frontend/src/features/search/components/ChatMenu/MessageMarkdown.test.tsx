import { ThemeProvider } from "@mui/material/styles";
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { globalTheme } from "@app/theme";

import { MessageMarkdown } from "./MessageMarkdown";

const ANSWER = "A **finished** paragraph.\n\nThe *tail* still";

const renderMarkdown = (text: string, isStreaming: boolean) =>
    render(
        <ThemeProvider theme={globalTheme}>
            <MessageMarkdown text={text} isStreaming={isStreaming} />
        </ThemeProvider>,
    ).container;

describe("MessageMarkdown", () => {
    it("parses the blocks of a streaming answer that are complete", () => {
        const container = renderMarkdown(ANSWER, true);

        expect(container.querySelector("strong")?.textContent).toBe("finished");
    });

    it("leaves the block of a streaming answer still being written as text", () => {
        const container = renderMarkdown(ANSWER, true);

        expect(container.querySelector("em")).toBeNull();
        expect(container.textContent).toContain("The *tail* still");
    });

    it("parses the whole answer once it is no longer streaming", () => {
        const container = renderMarkdown(ANSWER, false);

        expect(container.querySelector("em")?.textContent).toBe("tail");
    });
});
