// Creating type of const instead of enum, since they are not erasable syntax

export const DialogType = {
    About: "About",
    AddTagsDialog: "addTagsDialog",
    CreateArchive: "createArchive",
    DeleteCustomQuery: "deleteCustomQuery",
    DeleteTagGlobally: "deleteTagGlobally",
    FileDetail: "fileDetail",
    ImageDescription: "imageDescriptionDialog",
    Summary: "summary",
    Translation: "translation",
    EncryptionKeyInfo: "encryptionKeyInfo",
    UploadFile: "uploadFile",
} as const;
export type DialogType = (typeof DialogType)[keyof typeof DialogType];

export const TaskStatus = {
    Success: "success",
    Warning: "warning",
    Error: "error",
} as const;
export type TaskStatus = (typeof TaskStatus)[keyof typeof TaskStatus];

export const FileDetailTab = {
    Rendered: 0,
    Content: 1,
    Highlights: 2,
    RAW: 3,
    Summary: 4,
    Translations: 5,
    ImageDescription: 6,
} as const;
export type FileDetailTab = (typeof FileDetailTab)[keyof typeof FileDetailTab];

export const SummaryTab = {
    Summary: "summary",
    ImageDescription: "imageDescription",
} as const;
export type SummaryTab = (typeof SummaryTab)[keyof typeof SummaryTab];

export const FileRendererType = {
    Image: 0,
    Browser: 1,
    Office: 2,
    Email: 3,
};
export type FileRendererType =
    (typeof FileRendererType)[keyof typeof FileRendererType];

export const SearchQueryField = {
    Tags: "tags",
    Filename: "filename",
    Extension: "extension",
};
export type SearchQueryField =
    (typeof SearchQueryField)[keyof typeof SearchQueryField];
