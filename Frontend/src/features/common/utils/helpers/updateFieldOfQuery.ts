import { SearchQueryField } from "@features/common/utils/enums";

/**
 * Extract the unescaped values from an existing `field:(...)` or
 * `field:"value"` positive expression in the query, or [] if none is found.
 * Does not match `NOT field:...` expressions.
 */
const extractPositiveValues = (
    query: string,
    fieldNameSanitized: string,
): string[] => {
    const re = new RegExp(
        `(?<!NOT )${fieldNameSanitized}:(?:"((?:[^"\\\\]|\\\\.)*)"|\\(([^)]*)\\))`,
    );
    const m = query.match(re);
    if (!m) return [];
    if (m[1] !== undefined) {
        return [m[1].replace(/\\(["\\])/g, "$1")];
    }
    const values: string[] = [];
    const valueRe = /"((?:[^"\\]|\\.)*)"/g;
    let vm: RegExpExecArray | null;
    while ((vm = valueRe.exec(m[2])) !== null) {
        values.push(vm[1].replace(/\\(["\\])/g, "$1"));
    }
    return values;
};

/**
 * Extract the unescaped values from an existing `NOT field:(...)` or
 * `NOT field:"value"` expression in the query, or [] if none is found.
 */
const extractNegatedValues = (
    query: string,
    fieldNameSanitized: string,
): string[] => {
    const re = new RegExp(
        `NOT\\s+${fieldNameSanitized}:(?:"((?:[^"\\\\]|\\\\.)*)"|\\(([^)]*)\\))`,
    );
    const m = query.match(re);
    if (!m) return [];
    if (m[1] !== undefined) {
        return [m[1].replace(/\\(["\\])/g, "$1")];
    }
    const values: string[] = [];
    const valueRe = /"((?:[^"\\]|\\.)*)"/g;
    let vm: RegExpExecArray | null;
    while ((vm = valueRe.exec(m[2])) !== null) {
        values.push(vm[1].replace(/\\(["\\])/g, "$1"));
    }
    return values;
};

const escapeForRegex = (field: string): string =>
    field.replace(/([-.\s\\:])/g, "\\$1");

const fieldStripRegex = (field: string): RegExp =>
    new RegExp(
        `\\s*(?:NOT\\s+)?${escapeForRegex(field)}:(?:"(?:[^"\\\\]|\\\\.)*"|\\([^)]*\\)|[\\[{][^\\]}\n]*[\\]}]|\\S+)\\s*`,
        "g",
    );

export const updateFieldOfQuery = (
    previousQuery: string,
    fieldName: SearchQueryField,
    fieldValue: string | string[],
    noQuote = false,
    negate = false,
    accumulate = false,
    clearFields: string[] = [],
): string => {
    const newFieldNameSanitized = fieldName.replace(/([-\s\\:])/g, "\\$1");
    const newFieldNameRegex = escapeForRegex(fieldName);
    // Always convert fieldValue to string array
    let fieldValueArray = Array.isArray(fieldValue) ? fieldValue : [fieldValue];

    // When accumulating, extend an existing positive filter for this field
    // rather than replacing it, so repeated ctrl+clicks add more values.
    if (accumulate && !negate && !noQuote) {
        const existing = extractPositiveValues(
            previousQuery,
            newFieldNameRegex,
        );
        if (existing.length > 0) {
            fieldValueArray = Array.from(
                new Set([...existing, ...fieldValueArray]),
            );
        }
    }

    // When negating, extend an existing NOT filter for this field rather than
    // replacing it, so repeated "others" clicks accumulate exclusions.
    if (negate && !noQuote) {
        const existing = extractNegatedValues(previousQuery, newFieldNameRegex);
        if (existing.length > 0) {
            const merged = Array.from(
                new Set([...existing, ...fieldValueArray]),
            );
            fieldValueArray = merged;
        }
    }

    // Regex to match both formats (with optional NOT prefix):
    // fieldName:"value" OR fieldName:("value1" OR "value2" ...) OR fieldName:[start TO end] OR fieldName:*
    // Also handles Lucene range variants: [a TO b], [a TO b}, {a TO b], {a TO b}
    const fieldRegex = fieldStripRegex(fieldName);
    const replaced = previousQuery.replace(fieldRegex, " ").trim();

    // Strip caller-specified fields from the query.
    let withConflictsRemoved = replaced;
    for (const field of clearFields) {
        const conflictRegex = fieldStripRegex(field);
        withConflictsRemoved = withConflictsRemoved
            .replace(conflictRegex, " ")
            .trim();
    }

    // A bare `*` with nothing else is a match-all placeholder; drop it so it
    // doesn't accumulate as cruft alongside real field filters.
    const previousQueryReplaced =
        withConflictsRemoved === "*" ? "" : withConflictsRemoved;

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
