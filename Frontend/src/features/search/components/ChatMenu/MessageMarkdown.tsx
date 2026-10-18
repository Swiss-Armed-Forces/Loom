import { Typography } from "@mui/material";
import React from "react";
import Markdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";

import "./hljs-theme";

// Restricting rehype-highlight to a subset of languages does not shrink the
// bundle: it imports lowlight's `common` at module scope, so all 37 grammars
// ship whether or not `languages` is passed, and a subset only adds to them.
const REMARK_PLUGINS = [remarkGfm];
const REHYPE_PLUGINS = [rehypeHighlight];

/**
 * Renders one message's markdown.
 *
 * Parsing and highlighting a message costs several milliseconds, so this is
 * memoised on the text alone — a re-render for any other reason (theme, hover,
 * a sibling message changing) reuses the previous output.
 */
export const MessageMarkdown = React.memo(({ text }: { text: string }) => (
    <Typography variant="body2" component="div">
        <Markdown remarkPlugins={REMARK_PLUGINS} rehypePlugins={REHYPE_PLUGINS}>
            {text}
        </Markdown>
    </Typography>
));
MessageMarkdown.displayName = "MessageMarkdown";
