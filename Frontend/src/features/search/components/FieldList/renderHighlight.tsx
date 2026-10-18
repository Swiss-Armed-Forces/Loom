import { Fragment, ReactNode } from "react";

const PATTERN_HIGHLIGHT_TAG = /(<highlight>.*?<\/highlight>)/g;
const STRIP_TAGS = /<\/?highlight>/g;

/** Drops the `<highlight>` markers, leaving the plain field value. */
export const stripHighlightTags = (text: string): string =>
    text.replace(STRIP_TAGS, "");

/** Parses text with `<highlight>` tags into JSX, each marked span as an `<em>`.
 *  Shared by every field renderer so both layouts mark hits identically. */
export const renderHighlight = (text: string): ReactNode => {
    return text.split(PATTERN_HIGHLIGHT_TAG).map((part, i) => {
        if (part.startsWith("<highlight>")) {
            return (
                <em key={`${i}-${part.slice(0, 8)}`}>
                    {part.replace(STRIP_TAGS, "")}
                </em>
            );
        }
        return <Fragment key={`${i}-${part.slice(0, 8)}`}>{part}</Fragment>;
    });
};
