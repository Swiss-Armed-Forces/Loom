export const shouldShowSearchPanel = (
    activeTabFileId: string | null,
    isTourActive: boolean,
): boolean => isTourActive || activeTabFileId === null;

export const shouldShowFilePanel = (
    fileId: string,
    activeTabFileId: string | null,
    isTourActive: boolean,
): boolean => !isTourActive && activeTabFileId === fileId;
