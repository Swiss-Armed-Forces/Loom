import { Box, Typography } from "@mui/material";
import React from "react";
import Markdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";

import { splitStreamedMarkdown } from "./chatbotUtils";
import "./hljs-theme";

// Restricting rehype-highlight to a subset of languages does not shrink the
// bundle: it imports lowlight's `common` at module scope, so all 37 grammars
// ship whether or not `languages` is passed, and a subset only adds to them.
const REMARK_PLUGINS = [remarkGfm];
const REHYPE_PLUGINS = [rehypeHighlight];

// The block still being written keeps the line breaks it arrives with, no
// markdown having been applied to it, and sits a paragraph's distance below
// the blocks that are already parsed.
const TAIL_SX = { whiteSpace: "pre-wrap" } as const;
const TAIL_BELOW_STABLE_SX = { ...TAIL_SX, mt: 1 } as const;

/**
 * Parses and highlights one stretch of markdown.
 *
 * Memoised on its text, so the settled part of an answer being streamed is
 * parsed once per completed block rather than once per token.
 */
const ParsedMarkdown = React.memo(({ text }: { text: string }) => (
    <Markdown remarkPlugins={REMARK_PLUGINS} rehypePlugins={REHYPE_PLUGINS}>
        {text}
    </Markdown>
));
ParsedMarkdown.displayName = "ParsedMarkdown";

/**
 * Renders one message's markdown.
 *
 * Parsing and highlighting a message costs time proportional to its length,
 * so this is memoised on the text alone — a re-render for any other reason
 * (theme, hover, a sibling message changing) reuses the previous output.
 *
 * A streaming message's text grows by a token at a time, and parsing all of
 * it per token costs time quadratic in the length of the answer. While
 * `isStreaming` holds, only the blocks that are complete are parsed and the
 * block still being written is shown as plain text; the whole answer is
 * parsed once when the stream ends.
 */
export const MessageMarkdown = React.memo(
    ({
        text,
        isStreaming = false,
    }: {
        text: string;
        isStreaming?: boolean;
    }) => {
        const { stable, tail } = isStreaming
            ? splitStreamedMarkdown(text)
            : { stable: text, tail: "" };

        return (
            <Typography variant="body2" component="div">
                {stable !== "" && <ParsedMarkdown text={stable} />}
                {tail !== "" && (
                    <Box sx={stable === "" ? TAIL_SX : TAIL_BELOW_STABLE_SX}>
                        {tail}
                    </Box>
                )}
            </Typography>
        );
    },
);
MessageMarkdown.displayName = "MessageMarkdown";
