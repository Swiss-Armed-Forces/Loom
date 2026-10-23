import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import type { GetFilePreviewResponse, PreviewField } from "@app/api/index";

/**
 * Selectable card fields that are drawn as marks rather than as text.
 *
 * Everything they draw is on the preview the card already holds, and all of
 * it is either a list a card has no room for - a mail with nine attachments
 * is not nine lines of filenames on a search result - or a state the header
 * only shows when it is worth showing. What a reader scanning a list wants
 * from any of them is whether there is anything there, so that is what these
 * draw: a row of icons, lit for whatever the file has.
 *
 * Grouped rather than one field per icon: four fields that each cost a line
 * and draw a single glyph is four lines to say what one line says.
 *
 * They are offered beside the fields the backend lists and chosen the same
 * way, but they are not backend fields: nothing is requested for them, and
 * `apiPreviewFields` keeps them out of the preview request.
 */
export const INDICATOR_FIELD_IDS = [
    "loom:icons",
    "loom:status",
    "loom:state",
] as const;

export type IndicatorFieldId = (typeof INDICATOR_FIELD_IDS)[number];

/** The `loom:` prefix is not a namespace the backend uses, so a field of its
 *  own can never collide with one of these. */
export const isIndicatorField = (id: string): id is IndicatorFieldId =>
    (INDICATOR_FIELD_IDS as readonly string[]).includes(id);

/**
 * The selection, less the fields the backend knows nothing about.
 *
 * Used for the preview request and for the field set recorded against the
 * cached preview, so the two agree: picking up an indicator field asks for no
 * new data, and must therefore not invalidate a preview already in hand.
 */
export const apiPreviewFields = (previewFields: string[]): string[] =>
    previewFields.filter((id) => !isIndicatorField(id));

/** Translation keys for the labels, resolved where the fields are offered. */
export const INDICATOR_FIELD_LABEL_KEYS: Record<IndicatorFieldId, string> = {
    "loom:icons": "sideMenu.customization.indicator.icons",
    "loom:status": "sideMenu.customization.indicator.status",
    "loom:state": "sideMenu.customization.indicator.state",
};

/** One mark a file may carry. The icon for each lives beside the renderer. */
export type IndicatorMark =
    | "attachments"
    | "tags"
    | "flagged"
    | "unseen"
    | "truncated"
    | "skipped"
    | "spam";

/** The marks of each field, in the order they are drawn. */
const MARKS_OF: Record<IndicatorFieldId, IndicatorMark[]> = {
    // Tags last: the other three are one glyph each and the tag mark is the
    // one that stands for a list, so it reads as the tail of the row.
    "loom:icons": ["attachments", "flagged", "unseen", "tags"],
    "loom:status": ["truncated", "skipped", "spam"],
    "loom:state": [],
};

/** Whether a file carries a mark. */
const hasMark = (
    mark: IndicatorMark,
    preview: GetFilePreviewResponse,
): boolean => {
    switch (mark) {
        case "attachments":
            return (preview.attachmentsTotalCount ?? 0) > 0;
        case "tags":
            return (preview.tags?.length ?? 0) > 0;
        case "flagged":
            return preview.flagged;
        case "unseen":
            return !preview.seen;
        case "truncated":
            return preview.contentIsTruncated ?? false;
        case "skipped":
            return preview.attachmentsSkipped ?? false;
        case "spam":
            return preview.isSpam ?? false;
    }
};

/** The marks `fieldId` draws for `preview`, in order. */
export const indicatorMarks = (
    fieldId: IndicatorFieldId,
    preview: GetFilePreviewResponse,
): IndicatorMark[] =>
    MARKS_OF[fieldId].filter((mark) => hasMark(mark, preview));

/**
 * A backend label map with the indicator fields' own names merged in.
 *
 * `availablePreviewFields` is filled by the customization panel, so until a
 * reader has opened it once every label falls back to the raw field id. These
 * are ours and their names are known without asking anyone.
 */
export const withIndicatorLabels = (
    labels: Record<string, string>,
    label: (key: string) => string,
): Record<string, string> => ({
    ...labels,
    ...Object.fromEntries(
        INDICATOR_FIELD_IDS.map((id) => [
            id,
            label(INDICATOR_FIELD_LABEL_KEYS[id]),
        ]),
    ),
});

/** The three, as the selection list wants them. */
export const indicatorPreviewFields = (
    label: (key: string) => string,
): PreviewField[] =>
    INDICATOR_FIELD_IDS.map((id) => ({
        id,
        label: label(INDICATOR_FIELD_LABEL_KEYS[id]),
    }));

/**
 * Field id to the label to draw for it, with the grouped indicator columns
 * named - they stand for several fields each and so have no label of their own.
 */
export const useFieldLabels = (
    availableFields: { id: string; label: string }[],
): Record<string, string> => {
    const { t } = useTranslation();
    return useMemo(() => {
        const map: Record<string, string> = {};
        for (const field of availableFields) {
            map[field.id] = field.label;
        }
        return withIndicatorLabels(map, t);
    }, [availableFields, t]);
};
