import { SearchQueryField } from "@features/common/utils/enums";

export const updateFieldOfQuery = (
    previousQuery: string,
    fieldName: SearchQueryField,
    fieldValue: string | string[],
    noQuote = false,
    negate = false,
): string => {
    const newFieldNameSanitized = fieldName.replace(/([-\s\\:])/g, "\\$1");
    // Always convert fieldValue to string array
    const fieldValueArray = Array.isArray(fieldValue)
        ? fieldValue
        : [fieldValue];

    // Regex to match both formats (with optional NOT prefix):
    // fieldName:"value" OR fieldName:("value1" OR "value2" ...) OR fieldName:*
    const fieldRegex = new RegExp(
        `\\s*(?:NOT\\s+)?${newFieldNameSanitized}:(?:"(?:[^"\\\\]|\\\\.)*"|\\([^)]*\\)|\\S+)\\s*`,
        "g",
    );
    const previousQueryReplaced = previousQuery.replace(fieldRegex, " ").trim();

    // Empty array: remove the field from the query entirely.
    if (fieldValueArray.length === 0) return previousQueryReplaced;

    // Sanitize each value in the array
    const sanitizedValues = fieldValueArray.map((value) =>
        value.replace(/(["\\])/g, "\\$1"),
    );

    // Create field entry with OR logic for multiple values
    let fieldEntry: string;
    if (noQuote) {
        if (sanitizedValues.length > 1) {
            throw new Error(
                "updateFieldOfQuery: noQuote does not support multiple values",
            );
        }
        fieldEntry = `${newFieldNameSanitized}:${sanitizedValues[0]}`;
    } else if (sanitizedValues.length === 1) {
        fieldEntry = `${newFieldNameSanitized}:"${sanitizedValues[0]}"`;
    } else {
        const orValues = sanitizedValues
            .map((value) => `"${value}"`)
            .join(" OR ");
        fieldEntry = `${newFieldNameSanitized}:(${orValues})`;
    }

    if (negate) {
        fieldEntry = `NOT ${fieldEntry}`;
    }

    return (
        fieldEntry +
        (previousQueryReplaced.length > 0 ? " " : "") +
        previousQueryReplaced
    );
};
