export const DemoUnavailableFeature = {
    ArchiveImport: "archiveImport",
    BackendServices: "backendServices",
    FileUpload: "fileUpload",
    TaskDetails: "taskDetails",
} as const;

export type DemoUnavailableFeature =
    (typeof DemoUnavailableFeature)[keyof typeof DemoUnavailableFeature];
