export const updateTagOfQuery = (
    previousQuery: string,
    newTag: string | string[],
): string => {
    return updateFieldOfQuery(previousQuery, "tags", newTag);
};

export const updateWhenOfQuery = (
    previousQuery: string,
    newWhen: string | string[],
): string => {
    return updateFieldOfQuery(previousQuery, "when", newWhen);
};

export const updateFilenameOfQuery = (
    previousQuery: string,
    newFilename: string | string[],
): string => {
    return updateFieldOfQuery(previousQuery, "filename", newFilename);
};

export const updateFileExtensionOfQuery = (
    previousQuery: string,
    newFileExtension: string | string[],
): string => {
    return updateFieldOfQuery(previousQuery, "extension", newFileExtension);
};

export const updateFieldOfQuery = (
    previousQuery: string,
    fieldName: string,
    fieldValue: string | string[],
): string => {
    const newFieldNameSanitized = fieldName.replace(/([-\s\\:])/g, "\\$1");
    // Always convert fieldValue to string array
    const fieldValueArray = Array.isArray(fieldValue)
        ? fieldValue
        : [fieldValue];

    // Sanitize each value in the array
    const sanitizedValues = fieldValueArray.map((value) =>
        value.replace(/(["\\])/g, "\\$1"),
    );

    // Create field entry with OR logic for multiple values
    let fieldEntry: string;
    if (sanitizedValues.length === 1) {
        fieldEntry = `${newFieldNameSanitized}:"${sanitizedValues[0]}"`;
    } else {
        const orValues = sanitizedValues
            .map((value) => `"${value}"`)
            .join(" OR ");
        fieldEntry = `${newFieldNameSanitized}:(${orValues})`;
    }

    // Regex to match both formats:
    // fieldName:"value" OR fieldName:("value1" OR "value2" ...)
    const fieldRegex = new RegExp(
        `\\s*${newFieldNameSanitized}:(?:"(?:[^"\\\\]|\\\\.)*"|\\([^)]*\\))\\s*`,
        "g",
    );
    const previousQueryReplaced = previousQuery.replace(fieldRegex, " ").trim();
    return (
        fieldEntry +
        (previousQueryReplaced.length > 0 ? " " : "") +
        previousQueryReplaced
    );
};
