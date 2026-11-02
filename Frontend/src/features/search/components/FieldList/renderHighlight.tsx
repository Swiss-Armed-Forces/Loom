import { Fragment, ReactNode } from "react";

const PATTERN_HIGHLIGHT_TAG = /(<highlight>.*?<\/highlight>)/g;
const STRIP_TAGS = /<\/?highlight>/g;

/** Drops the `<highlight>` markers, leaving the plain field value. */
export const stripHighlightTags = (text: string): string =>
    text.replace(STRIP_TAGS, "");

/** Parses text with `<highlight>` tags into JSX, each marked span as an `<em>`.
 *  Shared by every field renderer so both layouts mark hits identically.
 *  Module scope: it closes over nothing, and rebuilding it per render defeats
 *  memoisation of its callers. */
export const renderHighlight = (text: string): ReactNode =>
    text.split(PATTERN_HIGHLIGHT_TAG).map((part, i) => {
        if (part.startsWith("<highlight>")) {
            return (
                <em key={`${i}-${part.slice(0, 8)}`}>
                    {stripHighlightTags(part)}
                </em>
            );
        }
        return <Fragment key={`${i}-${part.slice(0, 8)}`}>{part}</Fragment>;
    });
