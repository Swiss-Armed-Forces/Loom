import { GetFilePreviewResponse } from "@app/api";

type ProcessingStatusPreview = Pick<
    GetFilePreviewResponse,
    "attachmentsSkipped" | "contentIsTruncated" | "state"
>;

export const hasVisibleProcessingStatus = (
    filePreview: ProcessingStatusPreview,
    isNarrow: boolean,
): boolean =>
    filePreview.state !== "processed" ||
    (!isNarrow &&
        (filePreview.contentIsTruncated ||
            (filePreview.attachmentsSkipped ?? false)));
