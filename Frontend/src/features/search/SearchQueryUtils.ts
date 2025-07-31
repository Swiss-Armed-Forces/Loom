export const updateTagOfQuery = (
    previousQuery: string,
    newTag: string,
): string => {
    return updateFieldOfQuery(previousQuery, "tags", newTag);
};

export const updateWhenOfQuery = (
    previousQuery: string,
    newWhen: string,
): string => {
    return updateFieldOfQuery(previousQuery, "when", newWhen);
};

export const updateFilenameOfQuery = (
    previousQuery: string,
    newFilename: string,
): string => {
    return updateFieldOfQuery(previousQuery, "filename", newFilename);
};

export const updateFileExtensionOfQuery = (
    previousQuery: string,
    newFileExtension: string,
): string => {
    return updateFieldOfQuery(previousQuery, "extension", newFileExtension);
};

export const updateFieldOfQuery = (
    previousQuery: string,
    fieldName: string,
    fieldValue: string,
): string => {
    const newFieldNameSanitized = fieldName.replace(/([-\s\\:])/g, "\\$1");
    const newFieldValueSanitized = fieldValue.replace(/(["\\])/g, "\\$1");
    const fieldRegex = new RegExp(
        `${newFieldNameSanitized}:"(?:[^"\\\\]|\\\\.)*"`,
    );
    const previousQueryReplaced = previousQuery.replace(fieldRegex, "").trim();
    return (
        previousQueryReplaced +
        (previousQueryReplaced.length > 0 ? " " : "") +
        `${newFieldNameSanitized}:"${newFieldValueSanitized}"`
    );
};
