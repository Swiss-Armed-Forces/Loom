export const updateTagOfQuery = (
    previousQuery: string,
    newTag: string,
): string => {
    return replaceSectionIfExists(previousQuery, "tags", newTag);
};

export const updateWhenOfQuery = (
    previousQuery: string,
    newWhen: string,
): string => {
    return replaceSectionIfExists(previousQuery, "when", newWhen);
};

export const updateFilenameOfQuery = (
    previousQuery: string,
    newFilename: string,
): string => {
    return replaceSectionIfExists(
        previousQuery,
        "filename",
        `"${newFilename.replaceAll('"', '\\"')}"`,
    );
};

export const updateFileExtensionOfQuery = (
    previousQuery: string,
    newFileExtension: string,
): string => {
    return replaceSectionIfExists(previousQuery, "extension", newFileExtension);
};

export const updateFieldOfQuery = (
    previousQuery: string,
    newFieldName: string,
    newFieldValue: string,
): string => {
    return replaceSectionIfExists(
        previousQuery,
        newFieldName,
        `"${newFieldValue}"`,
    );
};

export const replaceSectionIfExists = (
    query: string,
    sectionName: string,
    newValue: string,
) => {
    let resultQuery: string;
    const sectionPrefix = `${sectionName}:`;
    const newSectionBlock = sectionPrefix + newValue;
    if (query.includes(sectionPrefix)) {
        resultQuery = query.replace(
            new RegExp(sectionPrefix + "((\\(.+\\))|([^ ]*))"),
            newSectionBlock,
        );
    } else {
        resultQuery = `${query} ${newSectionBlock}`;
    }
    return resultQuery.trim();
};
