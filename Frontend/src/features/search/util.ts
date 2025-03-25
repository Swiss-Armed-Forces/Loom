import { format, parseISO } from "date-fns";

const tagTypeColors = new Map<string, string>([
    ["manual", "#ffb74d"],
    ["source", "#64b5f6"],
    ["auto", "#aed581"],
]);

export const tagTypeToBackgroundColor = (tagType: string): string => {
    return tagTypeColors.get(tagType) || "rgba(0, 0, 0, 0.08)";
};

export const bytesToMegaBytes = (bytesCount: number) => {
    return bytesCount / (1024 * 1024);
};

export const fileSizeIsNotTooLarge = (fileSize: number) => {
    const maxFileSize = 3; //MB
    return bytesToMegaBytes(fileSize) > maxFileSize;
};

export const getFileSize = (file: File[]) => {
    if (file && file[0]) {
        return file[0].size;
    }

    return null;
};

export const fileIsTooLarge = (file: File[]) => {
    const size = getFileSize(file);

    if (size == null) return false;

    return fileSizeIsNotTooLarge(size);
};

export const formatFileSize = (sizeInBytes: number) => {
    const sizeInKBytes = sizeInBytes / 1024;

    if (sizeInKBytes < 1) {
        return `${sizeInBytes} Bytes`;
    }

    const sizeInMBytes = sizeInKBytes / 1024;
    if (sizeInMBytes < 1) {
        return `${sizeInKBytes.toFixed(2)} KB`;
    }

    const sizeInGbytes = sizeInMBytes / 1024;
    if (sizeInGbytes < 1) {
        return `${sizeInMBytes.toFixed(2)} MB`;
    }

    return `${sizeInGbytes.toFixed(2)} GB`;
};

export const getFormattedDateTime = (inputDate: string) => {
    const date = parseISO(inputDate);
    return format(date, "yyyy-dd-MM HH:mm");
};
