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
