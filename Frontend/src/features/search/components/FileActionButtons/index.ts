import { GetFilePreviewResponse } from "@app/api";

import { AddTagsButton } from "./AddTagsButton";
import { CreateArchiveButton } from "./CreateArchiveButton";
import { DownloadButton } from "./DownloadButton";
import { ImageDescriptionButton } from "./ImageDescriptionButton";
import { ReIndexButton } from "./ReIndexButton";
import { ShareButton } from "./ShareButton";
import { SummaryButton } from "./SummaryButton";
import { TranslationButton } from "./TranslationButton";
import { UpdateFlaggedButton } from "./UpdateFlaggedButton";
import { UpdateHiddenButton } from "./UpdateHiddenButton";
import { UpdateSeenButton } from "./UpdateSeenButton";
import { UploadFileButton } from "./UploadFileButton";
import { ViewDetailButton } from "./ViewDetailButton";

export interface FileActionButtonProps {
    filePreview?: GetFilePreviewResponse;
    disabled?: boolean;
    iconOnly?: boolean;
}

export {
    AddTagsButton,
    CreateArchiveButton,
    DownloadButton,
    ImageDescriptionButton,
    ReIndexButton,
    ShareButton,
    SummaryButton,
    TranslationButton,
    UpdateFlaggedButton,
    UpdateHiddenButton,
    UpdateSeenButton,
    UploadFileButton,
    ViewDetailButton,
};
