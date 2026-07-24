import { ExpandLess, ExpandMore } from "@mui/icons-material";
import { Box, Collapse, Typography } from "@mui/material";
import { useState } from "react";

const DEFAULT_PREVIEW_LINES = 15;
const DEFAULT_PREVIEW_CHARACTERS = 400;

const collapsedBarSx = {
    px: 1.5,
    py: 0.5,
    display: "flex",
    alignItems: "center",
    gap: 0.5,
    cursor: "pointer",
    bgcolor: "action.hover",
    borderBottom: 1,
    borderColor: "divider",
    userSelect: "none" as const,
    "&:hover": { bgcolor: "action.selected" },
};

const expandedBarSx = {
    ...collapsedBarSx,
    borderBottom: 0,
    borderTop: 1,
    borderColor: "divider",
};

interface ExpandableTextBlockProps {
    text: string;
    title: string;
    color?:
        | "error"
        | "inherit"
        | "primary"
        | "secondary"
        | "success"
        | "text.primary"
        | "text.secondary"
        | "warning";
    previewDirection?: "head" | "tail";
    previewLineCount?: number;
    previewCharacterCount?: number;
}

const createPreviewText = ({
    text,
    previewDirection,
    previewLineCount,
    previewCharacterCount,
}: {
    text: string;
    previewDirection: "head" | "tail";
    previewLineCount: number;
    previewCharacterCount: number;
}): string => {
    const lines = text.split("\n");
    const linePreview =
        previewDirection === "head"
            ? lines.slice(0, previewLineCount).join("\n")
            : lines.slice(-previewLineCount).join("\n");

    if (linePreview.length <= previewCharacterCount) {
        return linePreview;
    }

    return previewDirection === "head"
        ? `${linePreview.slice(0, previewCharacterCount)}...`
        : `...${linePreview.slice(-previewCharacterCount)}`;
};

export const ExpandableTextBlock = ({
    text,
    title,
    color = "text.primary",
    previewDirection = "head",
    previewLineCount = DEFAULT_PREVIEW_LINES,
    previewCharacterCount = DEFAULT_PREVIEW_CHARACTERS,
}: ExpandableTextBlockProps) => {
    const [expanded, setExpanded] = useState(false);
    const lines = text.split("\n");
    const previewText = createPreviewText({
        text,
        previewDirection,
        previewLineCount,
        previewCharacterCount,
    });
    const isTruncated = previewText !== text;
    const hiddenLineCount = Math.max(lines.length - previewLineCount, 0);
    const hiddenCharacterCount = Math.max(text.length - previewText.length, 0);

    const bodySx = {
        fontFamily: "monospace",
        whiteSpace: "pre-wrap",
        fontSize: "0.75rem",
        p: 1.5,
    };

    const collapsedLabel =
        hiddenLineCount > 0
            ? `${hiddenLineCount} lines hidden — show full ${title.toLowerCase()}`
            : `${hiddenCharacterCount} characters hidden — show full ${title.toLowerCase()}`;

    return (
        <Box
            sx={{
                mt: 0.5,
                border: 1,
                borderColor: "divider",
                borderRadius: 1,
                overflow: "hidden",
            }}
        >
            <Box
                sx={{
                    px: 1.5,
                    py: 0.75,
                    borderBottom: 1,
                    borderColor: "divider",
                }}
            >
                <Typography variant="caption" color="text.secondary">
                    {title}
                </Typography>
            </Box>

            {isTruncated && (
                <Box
                    sx={collapsedBarSx}
                    onClick={() => setExpanded((value) => !value)}
                >
                    {expanded ? (
                        <ExpandLess fontSize="small" color="disabled" />
                    ) : (
                        <ExpandMore fontSize="small" color="disabled" />
                    )}
                    <Typography variant="caption" color="text.secondary">
                        {expanded ? "Show less" : collapsedLabel}
                    </Typography>
                </Box>
            )}

            <Collapse in={expanded || !isTruncated}>
                <Typography variant="body2" color={color} sx={bodySx}>
                    {text}
                </Typography>
            </Collapse>

            {!expanded && isTruncated && (
                <Typography variant="body2" color={color} sx={bodySx}>
                    {previewText}
                </Typography>
            )}

            {isTruncated && expanded && (
                <Box sx={expandedBarSx} onClick={() => setExpanded(false)}>
                    <ExpandLess fontSize="small" color="disabled" />
                    <Typography variant="caption" color="text.secondary">
                        Show less
                    </Typography>
                </Box>
            )}
        </Box>
    );
};
