import { GetFilePreviewResponse } from "@app/api";

type ProcessingStatusPreview = Pick<
    GetFilePreviewResponse,
    "attachmentsSkipped" | "contentIsTruncated" | "state"
>;

export const hasVisibleProcessingStatus = (
    filePreview: ProcessingStatusPreview,
    isMobile: boolean,
): boolean =>
    filePreview.state !== "processed" ||
    (!isMobile &&
        (filePreview.contentIsTruncated ||
            (filePreview.attachmentsSkipped ?? false)));
