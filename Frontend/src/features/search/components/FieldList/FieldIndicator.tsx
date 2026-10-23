import {
    AttachFile,
    ContentCut,
    FiberManualRecord,
    Flag,
    Label,
    LinkOff,
    Whatshot,
} from "@mui/icons-material";
import { Box, Chip, SvgIconProps, Typography } from "@mui/material";
import { ComponentType } from "react";
import { useTranslation } from "react-i18next";

import { GetFilePreviewResponse } from "@app/api";

import {
    INDICATOR_FIELD_LABEL_KEYS,
    IndicatorFieldId,
    IndicatorMark,
    indicatorMarks,
} from "./indicatorFields";

/** The same icons these things are drawn with elsewhere on a card, so a mark
 *  reads as a smaller version of what it stands for. */
const ICONS: Record<IndicatorMark, ComponentType<SvgIconProps>> = {
    attachments: AttachFile,
    tags: Label,
    flagged: Flag,
    unseen: FiberManualRecord,
    truncated: ContentCut,
    skipped: LinkOff,
    spam: Whatshot,
};

const TOOLTIP_KEYS: Record<IndicatorMark, string> = {
    attachments: "fieldSections.mark.attachments",
    tags: "fieldSections.mark.tags",
    flagged: "fieldSections.mark.flagged",
    unseen: "fieldSections.mark.unseen",
    truncated: "fieldSections.mark.truncated",
    skipped: "fieldSections.mark.skipped",
    spam: "fieldSections.mark.spam",
};

/** Coloured only where the colour is the point; the rest read as text. The
 *  unseen dot is the amber one the folder tree already marks unseen with. */
const MARK_COLOUR: Partial<Record<IndicatorMark, string>> = {
    flagged: "error.main",
    spam: "error.main",
    unseen: "primary.main",
};

/** The same colours the header's state chip uses. */
const STATE_CHIP_COLOUR: Record<string, "warning" | "error"> = {
    started: "warning",
    reindexing: "warning",
    failed: "error",
};

const ROW_SX = {
    display: "flex",
    alignItems: "center",
    gap: "var(--loom-row-gap, 0.5rem)",
    minWidth: 0,
    height: "var(--loom-row-height, 1.5rem)",
    overflow: "hidden",
    lineHeight: "var(--loom-row-line-height, 1.4)",
} as const;
const LABEL_SX = { flexShrink: 0 } as const;
const BOLD_LABEL_SX = { flexShrink: 0, fontWeight: "bold" } as const;
const MARKS_SX = { display: "flex", alignItems: "center", gap: 0.5 } as const;
const ICON_SX = { fontSize: "1rem" } as const;
const STATE_CHIP_SX = { height: "1.25rem", fontSize: "0.7rem" } as const;

export interface FieldIndicatorProps {
    fieldId: IndicatorFieldId;
    filePreview: GetFilePreviewResponse;
    bold?: boolean;
    showName?: boolean;
}

/**
 * One of the grouped card fields, as a row of marks.
 *
 * Nothing is drawn for a mark the file does not carry - not a muted icon and
 * not the label on its own. The whole point is that a mark's presence is the
 * answer, so anything in its place would have to be read before it could be
 * dismissed. The row it would have taken is still held open; see `rowRhythm`.
 *
 * Counts never appear as numbers; that is what the card's own attachment and
 * tag rows are for. These answer one question, which is whether to go and
 * look.
 */
export const FieldIndicator = ({
    fieldId,
    filePreview,
    bold,
    showName = true,
}: FieldIndicatorProps) => {
    const { t } = useTranslation();
    // Resolved here rather than taken from `availablePreviewFields`: that list
    // is filled by the customization panel, so until a reader has opened the
    // panel once every card label falls back to the raw field id. These are
    // ours and their names are known without asking anyone.
    const field = t(INDICATOR_FIELD_LABEL_KEYS[fieldId]);
    const marks = indicatorMarks(fieldId, filePreview);
    // The processing state is a value rather than a presence, so it is drawn
    // as the chip the header draws it as.
    const state = fieldId === "loom:state" ? filePreview.state : null;

    if (marks.length === 0 && !state) return <Box sx={ROW_SX} />;

    return (
        <Box sx={ROW_SX}>
            {showName && (
                <Typography
                    variant="caption"
                    component="span"
                    color="text.secondary"
                    sx={bold ? BOLD_LABEL_SX : LABEL_SX}
                >
                    {`${field}:`}
                </Typography>
            )}
            <Box sx={MARKS_SX}>
                {marks.map((mark) => {
                    const Icon = ICONS[mark];
                    return (
                        <Icon
                            key={mark}
                            titleAccess={t(TOOLTIP_KEYS[mark])}
                            sx={{
                                ...ICON_SX,
                                color: MARK_COLOUR[mark] ?? "text.secondary",
                            }}
                        />
                    );
                })}
                {state && (
                    <Chip
                        size="small"
                        label={state}
                        variant="outlined"
                        color={STATE_CHIP_COLOUR[state] ?? "default"}
                        sx={STATE_CHIP_SX}
                    />
                )}
            </Box>
        </Box>
    );
};
