import type { DemoDocument } from "./repository";

interface QueryModifier {
    distance: number;
    kind: "fuzzy" | "proximity";
}

interface Predicate {
    field?: string;
    kind: "predicate";
    modifier?: QueryModifier;
    quoted: boolean;
    value: string;
}

type QueryNode =
    | { kind: "and" | "or"; left: QueryNode; right: QueryNode }
    | { kind: "not"; operand: QueryNode }
    | Predicate;

type QueryToken =
    | { kind: "and" | "or" | "not" | "rightParenthesis" }
    | { kind: "leftParenthesis"; field?: string }
    | Predicate;

interface ReadValue {
    modifier?: QueryModifier;
    next: number;
    quoted: boolean;
    value: string;
}

interface ReadField {
    field: string;
    next: number;
}

export class DemoQueryError extends Error {}

const FIELD_CHARACTER = /[a-z0-9_.-]/i;
const DATE_FIELDS = new Set([
    "uploaded",
    "uploaded_datetime",
    "created",
    "modified",
    "tika_meta.dcterms_created",
    "tika_meta.pdf_docinfo_created",
    "tika_meta.dcterms_modified",
    "tika_meta.pdf_docinfo_modified",
]);

const readQuotedValue = (query: string, start: number): ReadValue => {
    let value = "";
    let index = start + 1;
    while (index < query.length) {
        const character = query[index];
        if (character === "\\" && index + 1 < query.length) {
            value += query[index + 1];
            index += 2;
            continue;
        }
        if (character === '"') {
            index += 1;
            const proximity = query.slice(index).match(/^~(\d+)/);
            const distance = proximity ? Number(proximity[1]) : undefined;
            if (distance !== undefined && !Number.isSafeInteger(distance))
                throw new DemoQueryError(
                    "Phrase proximity must be a safe integer",
                );
            return {
                modifier:
                    distance !== undefined
                        ? {
                              distance,
                              kind: "proximity",
                          }
                        : undefined,
                next: index + (proximity?.[0].length ?? 0),
                quoted: true,
                value,
            };
        }
        value += character;
        index += 1;
    }
    throw new DemoQueryError("Unterminated quoted value");
};

const readRange = (query: string, start: number): ReadValue => {
    const closingIndex = query.slice(start + 1).search(/[\]}]/);
    if (closingIndex < 0) throw new DemoQueryError("Unterminated range");
    const end = start + closingIndex + 2;
    return { next: end, value: query.slice(start, end), quoted: false };
};

const readPlainValue = (query: string, start: number): ReadValue => {
    let index = start;
    while (index < query.length && !/[\s()]/.test(query[index])) index += 1;
    const rawValue = query.slice(start, index);
    const fuzzy = rawValue.match(/^(.+)~(\d+)$/);
    if (fuzzy && Number(fuzzy[2]) > 2)
        throw new DemoQueryError("Fuzzy distance must be between 0 and 2");
    return {
        modifier: fuzzy
            ? { distance: Number(fuzzy[2]), kind: "fuzzy" }
            : undefined,
        next: index,
        value: fuzzy ? fuzzy[1] : rawValue,
        quoted: false,
    };
};

const readRegexValue = (query: string, start: number): ReadValue => {
    let index = start + 1;
    while (index < query.length) {
        if (query[index] === "\\" && index + 1 < query.length) {
            index += 2;
            continue;
        }
        if (query[index] === "/")
            return {
                next: index + 1,
                quoted: false,
                value: query.slice(start, index + 1),
            };
        index += 1;
    }
    throw new DemoQueryError("Unterminated regular expression");
};

const readValue = (query: string, start: number): ReadValue => {
    if (query[start] === '"') return readQuotedValue(query, start);
    if (query[start] === "[" || query[start] === "{")
        return readRange(query, start);
    if (query[start] === "/") return readRegexValue(query, start);
    return readPlainValue(query, start);
};

const readField = (query: string, start: number): ReadField | undefined => {
    let field = "";
    let index = start;
    while (index < query.length) {
        const character = query[index];
        if (character === ":" && field) return { field, next: index + 1 };
        if (character === "\\" && ["*", "?"].includes(query[index + 1])) {
            field += query[index + 1];
            index += 2;
            continue;
        }
        if (
            FIELD_CHARACTER.test(character) ||
            character === "*" ||
            character === "?"
        ) {
            field += character;
            index += 1;
            continue;
        }
        return undefined;
    }
    return undefined;
};

const predicateToken = (value: ReadValue, field?: string): Predicate => ({
    field,
    kind: "predicate",
    modifier: value.modifier,
    quoted: value.quoted,
    value: value.value,
});

const tokenize = (query: string): QueryToken[] => {
    const tokens: QueryToken[] = [];
    let index = 0;
    while (index < query.length) {
        if (/\s/.test(query[index])) {
            index += 1;
            continue;
        }
        if (query[index] === "(") {
            tokens.push({ kind: "leftParenthesis" });
            index += 1;
            continue;
        }
        if (query[index] === ")") {
            tokens.push({ kind: "rightParenthesis" });
            index += 1;
            continue;
        }

        const read = readField(query, index);
        if (read) {
            const { field } = read;
            index = read.next;
            if (query[index] === "(") {
                tokens.push({ kind: "leftParenthesis", field });
                index += 1;
                continue;
            }
            const value = readValue(query, index);
            if (!value.value)
                throw new DemoQueryError(`Missing value for ${field}`);
            tokens.push(predicateToken(value, field));
            index = value.next;
            continue;
        }

        const value = readValue(query, index);
        const operator = value.value.toLocaleUpperCase();
        if (
            !value.quoted &&
            (operator === "AND" || operator === "OR" || operator === "NOT")
        ) {
            tokens.push({
                kind: operator.toLocaleLowerCase() as "and" | "or" | "not",
            });
        } else if (value.value) {
            tokens.push(predicateToken(value));
        }
        index = value.next;
    }
    return tokens;
};

const scopeNode = (node: QueryNode, field: string): QueryNode => {
    if (node.kind === "predicate")
        return node.field ? node : { ...node, field };
    if (node.kind === "not")
        return { ...node, operand: scopeNode(node.operand, field) };
    return {
        ...node,
        left: scopeNode(node.left, field),
        right: scopeNode(node.right, field),
    };
};

class QueryParser {
    private index = 0;
    private readonly tokens: QueryToken[];

    public constructor(tokens: QueryToken[]) {
        this.tokens = tokens;
    }

    public parse(): QueryNode {
        if (this.tokens.length === 0)
            return {
                kind: "predicate",
                quoted: false,
                value: "*",
            };
        const result = this.parseOr();
        if (this.peek()) throw new DemoQueryError("Unexpected query token");
        return result;
    }

    private peek(): QueryToken | undefined {
        return this.tokens[this.index];
    }

    private parseOr(): QueryNode {
        let node = this.parseAnd();
        while (this.peek()?.kind === "or") {
            this.index += 1;
            node = { kind: "or", left: node, right: this.parseAnd() };
        }
        return node;
    }

    private parseAnd(): QueryNode {
        let node = this.parseUnary();
        while (true) {
            if (this.peek()?.kind === "and") {
                this.index += 1;
                node = { kind: "and", left: node, right: this.parseUnary() };
                continue;
            }
            if (
                this.peek()?.kind === "predicate" ||
                this.peek()?.kind === "leftParenthesis" ||
                this.peek()?.kind === "not"
            ) {
                node = { kind: "and", left: node, right: this.parseUnary() };
                continue;
            }
            return node;
        }
    }

    private parseUnary(): QueryNode {
        if (this.peek()?.kind !== "not") return this.parsePrimary();
        this.index += 1;
        return { kind: "not", operand: this.parseUnary() };
    }

    private parsePrimary(): QueryNode {
        const token = this.tokens[this.index];
        if (!token) throw new DemoQueryError("Missing query expression");
        this.index += 1;
        if (token.kind === "predicate") return token;
        if (token.kind !== "leftParenthesis")
            throw new DemoQueryError("Unexpected query operator");
        const node = this.parseOr();
        if (this.peek()?.kind !== "rightParenthesis")
            throw new DemoQueryError("Unterminated query group");
        this.index += 1;
        return token.field ? scopeNode(node, token.field) : node;
    }
}

const valuesByField = (document: DemoDocument): Record<string, string[]> => {
    const authorValues = document.authors;
    const secretValues = document.secrets;
    return {
        extension: [document.extension],
        tags: document.tags,
        state: [document.state],
        flagged: [String(document.flagged)],
        hidden: [String(document.hidden)],
        seen: [String(document.seen)],
        detected_language: [document.language],
        content_truncated: ["false"],
        attachments_skipped: ["false"],
        content: [document.content],
        summary: document.summary ? [document.summary] : [],
        image_description: document.imageDescription
            ? [document.imageDescription]
            : [],
        full_name: [document.path],
        "full_name.keyword": [document.path],
        full_path: [document.path],
        "full_path.keyword": [document.path],
        short_name: [document.name],
        "short_name.keyword": [document.name],
        filename: [document.name],
        file_type: [document.mimeType],
        magic_file_type: [document.mimeType],
        tika_file_type: [document.mimeType],
        archives: document.archiveIds,
        source: [document.source],
        size: [String(document.size)],
        uploaded: [document.uploadedAt],
        uploaded_datetime: [document.uploadedAt],
        created: [document.createdAt],
        modified: [document.modifiedAt],
        "tika_meta.dcterms_created": [document.createdAt],
        "tika_meta.pdf_docinfo_created": [document.createdAt],
        "tika_meta.dcterms_modified": [document.modifiedAt],
        "tika_meta.pdf_docinfo_modified": [document.modifiedAt],
        author: authorValues,
        "tika_meta.dc_creator": authorValues,
        "tika_meta.pdf_docinfo_creator": authorValues,
        "tika_meta.message_from_name": authorValues,
        "tika_meta.message_from": authorValues,
        "tika_meta.message_from_email": authorValues,
        "tika_meta.meta_last_author": authorValues,
        secrets: secretValues,
        "trufflehog_secrets.secret": secretValues,
        "ripsecrets_secrets.secret": secretValues,
    };
};

const TEXT_FIELDS_BY_ALIAS: Record<string, string[]> = {
    filename: [
        "short_name",
        "short_name.keyword",
        "full_name",
        "full_name.keyword",
        "full_path",
        "full_path.keyword",
    ],
    file_type: ["magic_file_type", "tika_file_type"],
    author: [
        "tika_meta.dc_creator",
        "tika_meta.pdf_docinfo_creator",
        "tika_meta.message_from_name",
        "tika_meta.message_from",
        "tika_meta.message_from_email",
        "tika_meta.meta_last_author",
    ],
    secrets: ["trufflehog_secrets.secret", "ripsecrets_secrets.secret"],
};

const NON_TEXT_FIELDS = new Set([
    "flagged",
    "hidden",
    "seen",
    "content_truncated",
    "attachments_skipped",
    "size",
    "uploaded",
    "uploaded_datetime",
    "created",
    "modified",
    "tika_meta.dcterms_created",
    "tika_meta.pdf_docinfo_created",
    "tika_meta.dcterms_modified",
    "tika_meta.pdf_docinfo_modified",
]);

const textValuesByField = (
    document: DemoDocument,
): Record<string, string[]> => {
    const fields = valuesByField(document);
    return Object.fromEntries(
        Object.entries(fields).filter(
            ([field, values]) =>
                !NON_TEXT_FIELDS.has(field) &&
                !Object.hasOwn(TEXT_FIELDS_BY_ALIAS, field) &&
                values.length > 0,
        ),
    );
};

export const valuesForField = (
    document: DemoDocument,
    field: string,
): string[] => valuesByField(document)[field] ?? [];

const unfieldedValues = (document: DemoDocument): string[] => [
    document.name,
    document.path,
    document.content,
    document.summary,
    ...document.tags,
    ...document.authors,
];

const parseComparable = (
    field: string | undefined,
    value: string,
    inclusiveUpperBound = false,
): number => {
    if (field === "size") {
        const match = value.match(/^([\d.]+)\s*([kmgt])?b?$/i);
        if (!match) return Number.NaN;
        const exponent = match[2]
            ? ["k", "m", "g", "t"].indexOf(match[2].toLocaleLowerCase()) + 1
            : 0;
        return Number(match[1]) * 1_000 ** exponent;
    }
    if (field && DATE_FIELDS.has(field)) {
        const timestamp = Date.parse(value);
        return inclusiveUpperBound && /^\d{4}-\d{2}-\d{2}$/.test(value)
            ? timestamp + 24 * 60 * 60 * 1_000 - 1
            : timestamp;
    }
    return Number(value);
};

const startOfDay = (date: Date): Date => {
    const result = new Date(date);
    result.setHours(0, 0, 0, 0);
    return result;
};

const relativeDateBounds = (
    value: string,
    nowTimestamp: number,
): [number, number] | undefined => {
    const now = new Date(nowTimestamp);
    const today = startOfDay(now);
    const lower = new Date(today);
    let upper = nowTimestamp;
    switch (value.toLocaleLowerCase()) {
        case "today":
            break;
        case "yesterday":
            lower.setDate(lower.getDate() - 1);
            upper = today.getTime();
            break;
        case "thisweek": {
            const daysSinceMonday = (lower.getDay() + 6) % 7;
            lower.setDate(lower.getDate() - daysSinceMonday);
            break;
        }
        case "thismonth":
            lower.setDate(1);
            break;
        case "thisyear":
            lower.setMonth(0, 1);
            break;
        default:
            return undefined;
    }
    return [lower.getTime(), upper];
};

const matchesRelativeDate = (
    candidates: string[],
    field: string | undefined,
    value: string,
    nowTimestamp: number,
): boolean | undefined => {
    if (!field || !DATE_FIELDS.has(field)) return undefined;
    const bounds = relativeDateBounds(value, nowTimestamp);
    if (!bounds) return undefined;
    return candidates.some((candidate) => {
        const timestamp = Date.parse(candidate);
        return timestamp >= bounds[0] && timestamp <= bounds[1];
    });
};

const matchesRange = (
    candidates: string[],
    field: string | undefined,
    expression: string,
): boolean => {
    const lowerBracket = expression[0];
    const upperBracket = expression.at(-1) ?? "";
    const bounds = expression.slice(1, -1).match(/^(.*?)\s+TO\s+(.*?)$/i);
    if (
        !["[", "{"].includes(lowerBracket) ||
        !["]", "}"].includes(upperBracket) ||
        !bounds
    )
        throw new DemoQueryError(`Invalid range: ${expression}`);
    const [, lower, upper] = bounds;
    return candidates.some((candidate) => {
        const candidateValue = parseComparable(field, candidate);
        const lowerValue =
            lower === "*" ? undefined : parseComparable(field, lower);
        const upperValue =
            upper === "*"
                ? undefined
                : parseComparable(field, upper, upperBracket === "]");
        if (
            (lowerValue !== undefined && Number.isNaN(lowerValue)) ||
            (upperValue !== undefined && Number.isNaN(upperValue))
        )
            throw new DemoQueryError(`Invalid range bound: ${expression}`);
        if (Number.isNaN(candidateValue)) return false;
        const lowerMatches =
            lowerValue === undefined ||
            (lowerBracket === "["
                ? candidateValue >= lowerValue
                : candidateValue > lowerValue);
        const upperMatches =
            upperValue === undefined ||
            (upperBracket === "]"
                ? candidateValue <= upperValue
                : candidateValue < upperValue);
        return lowerMatches && upperMatches;
    });
};

const matchesWildcard = (
    candidate: string,
    rawPattern: string,
    matchSubstring = true,
): boolean => {
    const wrappedPattern = matchSubstring ? "*" + rawPattern + "*" : rawPattern;
    const pattern = wrappedPattern.toLocaleLowerCase().replace(/\*+/g, "*");
    const value = candidate.toLocaleLowerCase();
    let previous = new Array<boolean>(value.length + 1).fill(false);
    previous[0] = true;

    for (const character of pattern) {
        const current = new Array<boolean>(value.length + 1).fill(false);
        if (character === "*") current[0] = previous[0];
        for (let index = 1; index <= value.length; index += 1) {
            current[index] =
                character === "*"
                    ? previous[index] || current[index - 1]
                    : previous[index - 1] &&
                      (character === "?" || character === value[index - 1]);
        }
        previous = current;
    }
    return previous[value.length];
};

const candidatesForField = (
    document: DemoDocument,
    field: string | undefined,
): string[] => {
    if (!field) return unfieldedValues(document);
    const fields = valuesByField(document);
    if (field === "*") return Object.values(fields).flat();
    if (!field.includes("*") && !field.includes("?"))
        return fields[field] ?? [];
    return Object.entries(fields)
        .filter(([name]) => matchesWildcard(name, field, false))
        .flatMap(([, values]) => values);
};

const compileRegex = (pattern: string): RegExp => {
    if (
        pattern.length > 256 ||
        ["(", ")", "[", "]", "{", "}", "|"].some((character) =>
            pattern.includes(character),
        ) ||
        /\\[1-9]/.test(pattern)
    )
        throw new DemoQueryError(
            "Regular expression uses syntax unsupported in demo mode",
        );
    try {
        return new RegExp(pattern, "iu");
    } catch {
        throw new DemoQueryError("Invalid regular expression");
    }
};

const words = (value: string): string[] =>
    value.toLocaleLowerCase().match(/[\p{L}\p{N}_]+/gu) ?? [];

interface TextRange {
    end: number;
    start: number;
}

interface WordRange extends TextRange {
    normalized: string;
}

const wordRanges = (value: string): WordRange[] =>
    [...value.matchAll(/[\p{L}\p{N}_]+/gu)].map((match) => ({
        end: (match.index ?? 0) + match[0].length,
        normalized: match[0].toLocaleLowerCase(),
        start: match.index ?? 0,
    }));

const levenshteinDistance = (
    leftValue: string,
    rightValue: string,
    maximum: number,
): number => {
    const left = [...leftValue];
    const right = [...rightValue];
    if (Math.abs(left.length - right.length) > maximum) return maximum + 1;
    let previous = right.map((_, index) => index + 1);
    previous.unshift(0);
    for (let leftIndex = 1; leftIndex <= left.length; leftIndex += 1) {
        const current = [leftIndex];
        let rowMinimum = current[0];
        for (let rightIndex = 1; rightIndex <= right.length; rightIndex += 1) {
            const substitution =
                previous[rightIndex - 1] +
                (left[leftIndex - 1] === right[rightIndex - 1] ? 0 : 1);
            const distance = Math.min(
                previous[rightIndex] + 1,
                current[rightIndex - 1] + 1,
                substitution,
            );
            current.push(distance);
            rowMinimum = Math.min(rowMinimum, distance);
        }
        if (rowMinimum > maximum) return maximum + 1;
        previous = current;
    }
    return previous[right.length];
};

const matchesFuzzy = (
    candidate: string,
    value: string,
    distance: number,
): boolean => {
    if (!Number.isInteger(distance) || distance < 0 || distance > 2)
        throw new DemoQueryError("Fuzzy distance must be between 0 and 2");
    const normalized = value.toLocaleLowerCase();
    return words(candidate).some(
        (candidateWord) =>
            levenshteinDistance(candidateWord, normalized, distance) <=
            distance,
    );
};

const matchesProximity = (
    candidate: string,
    phrase: string,
    distance: number,
): boolean => {
    if (!Number.isInteger(distance) || distance < 0)
        throw new DemoQueryError("Phrase proximity must not be negative");
    const phraseWords = words(phrase);
    const candidateWords = words(candidate);
    if (phraseWords.length === 0) return false;
    for (
        let start = 0;
        start <= candidateWords.length - phraseWords.length;
        start += 1
    ) {
        if (candidateWords[start] !== phraseWords[0]) continue;
        let candidateIndex = start;
        let slop = 0;
        let matched = true;
        for (
            let phraseIndex = 1;
            phraseIndex < phraseWords.length;
            phraseIndex += 1
        ) {
            const nextIndex = candidateWords.indexOf(
                phraseWords[phraseIndex],
                candidateIndex + 1,
            );
            if (nextIndex < 0) {
                matched = false;
                break;
            }
            slop += nextIndex - candidateIndex - 1;
            if (slop > distance) {
                matched = false;
                break;
            }
            candidateIndex = nextIndex;
        }
        if (matched) return true;
    }
    return false;
};

const isRange = (value: string): boolean =>
    ["[", "{"].includes(value[0]) &&
    ["]", "}"].includes(value.at(-1) ?? "") &&
    /\s+TO\s+/i.test(value);

const isComparison = (value: string): boolean => /^(>=|<=|>|<).+/.test(value);

const literalRanges = (candidate: string, value: string): TextRange[] => {
    if (!value) return [];
    const ranges: TextRange[] = [];
    const normalizedCandidate = candidate.toLocaleLowerCase();
    const normalizedValue = value.toLocaleLowerCase();
    let start = normalizedCandidate.indexOf(normalizedValue);
    while (start >= 0) {
        ranges.push({ start, end: start + value.length });
        start = normalizedCandidate.indexOf(
            normalizedValue,
            start + value.length,
        );
    }
    return ranges;
};

const regexRanges = (candidate: string, rawValue: string): TextRange[] => {
    const regexMatch = rawValue.match(/^\/(.*)\/$/);
    if (!regexMatch) return [];
    const expression = compileRegex(regexMatch[1]);
    const globalExpression = new RegExp(expression.source, "giu");
    return [...candidate.matchAll(globalExpression)]
        .filter((match) => match[0].length > 0)
        .map((match) => ({
            end: (match.index ?? 0) + match[0].length,
            start: match.index ?? 0,
        }));
};

const wildcardRanges = (candidate: string, value: string): TextRange[] => {
    if (value === "*" || !matchesWildcard(candidate, value)) return [];
    const literalParts = value.split(/[?*]+/).filter(Boolean);
    if (literalParts.length === 0)
        return candidate.length > 0
            ? [{ start: 0, end: candidate.length }]
            : [];
    return literalParts.flatMap((part) => literalRanges(candidate, part));
};

const fuzzyRanges = (
    candidate: string,
    value: string,
    distance: number,
): TextRange[] =>
    wordRanges(candidate)
        .filter(
            (candidateWord) =>
                levenshteinDistance(
                    candidateWord.normalized,
                    value.toLocaleLowerCase(),
                    distance,
                ) <= distance,
        )
        .map(({ start, end }) => ({ start, end }));

const proximityRanges = (
    candidate: string,
    phrase: string,
    distance: number,
): TextRange[] => {
    const phraseWords = words(phrase);
    const candidateWords = wordRanges(candidate);
    if (phraseWords.length === 0) return [];
    for (
        let start = 0;
        start <= candidateWords.length - phraseWords.length;
        start += 1
    ) {
        if (candidateWords[start].normalized !== phraseWords[0]) continue;
        const matched = [candidateWords[start]];
        let candidateIndex = start;
        let slop = 0;
        for (
            let phraseIndex = 1;
            phraseIndex < phraseWords.length;
            phraseIndex += 1
        ) {
            const nextIndex = candidateWords.findIndex(
                (word, index) =>
                    index > candidateIndex &&
                    word.normalized === phraseWords[phraseIndex],
            );
            if (nextIndex < 0) break;
            slop += nextIndex - candidateIndex - 1;
            if (slop > distance) break;
            matched.push(candidateWords[nextIndex]);
            candidateIndex = nextIndex;
        }
        if (matched.length === phraseWords.length)
            return matched.map(({ start: wordStart, end }) => ({
                start: wordStart,
                end,
            }));
    }
    return [];
};

const rangesForPredicate = (
    candidate: string,
    predicate: Predicate,
): TextRange[] => {
    const { modifier, value } = predicate;
    if (value === "*" || isRange(value) || isComparison(value)) return [];
    if (/^\/.+\/$/.test(value)) return regexRanges(candidate, value);
    if (modifier?.kind === "fuzzy")
        return fuzzyRanges(candidate, value, modifier.distance);
    if (modifier?.kind === "proximity")
        return proximityRanges(candidate, value, modifier.distance);
    if (value.includes("*") || value.includes("?"))
        return wildcardRanges(candidate, value);
    return literalRanges(candidate, value);
};

const matchesPredicate = (
    document: DemoDocument,
    predicate: Predicate,
    nowTimestamp: number,
): boolean => {
    const { field, modifier, value: rawValue } = predicate;
    const candidates = candidatesForField(document, field);
    if (rawValue === "*") return field ? candidates.length > 0 : true;
    if (
        ["[", "{"].includes(rawValue[0]) &&
        ["]", "}"].includes(rawValue.at(-1) ?? "") &&
        /\s+TO\s+/i.test(rawValue)
    )
        return matchesRange(candidates, field, rawValue);

    const relativeDateMatch = matchesRelativeDate(
        candidates,
        field,
        rawValue,
        nowTimestamp,
    );
    if (relativeDateMatch !== undefined) return relativeDateMatch;

    const comparison = rawValue.match(/^(>=|<=|>|<)(.+)$/);
    if (comparison) {
        const expected = parseComparable(field, comparison[2]);
        if (Number.isNaN(expected))
            throw new DemoQueryError(`Invalid comparison: ${rawValue}`);
        return candidates.some((candidate) => {
            const actual = parseComparable(field, candidate);
            if (comparison[1] === ">=") return actual >= expected;
            if (comparison[1] === "<=") return actual <= expected;
            if (comparison[1] === ">") return actual > expected;
            return actual < expected;
        });
    }

    const regexMatch = rawValue.match(/^\/(.*)\/$/);
    if (regexMatch) {
        const expression = compileRegex(regexMatch[1]);
        return candidates.some((candidate) => expression.test(candidate));
    }

    if (modifier?.kind === "fuzzy")
        return candidates.some((candidate) =>
            matchesFuzzy(candidate, rawValue, modifier.distance),
        );
    if (modifier?.kind === "proximity")
        return candidates.some((candidate) =>
            matchesProximity(candidate, rawValue, modifier.distance),
        );

    const value = rawValue;
    if (value.includes("*") || value.includes("?")) {
        return candidates.some((candidate) =>
            matchesWildcard(candidate, value),
        );
    }
    const normalized = value.toLocaleLowerCase();
    return candidates.some((candidate) =>
        candidate.toLocaleLowerCase().includes(normalized),
    );
};

const evaluate = (
    document: DemoDocument,
    node: QueryNode,
    nowTimestamp: number,
): boolean => {
    if (node.kind === "predicate")
        return matchesPredicate(document, node, nowTimestamp);
    if (node.kind === "not")
        return !evaluate(document, node.operand, nowTimestamp);
    if (node.kind === "and")
        return (
            evaluate(document, node.left, nowTimestamp) &&
            evaluate(document, node.right, nowTimestamp)
        );
    return (
        evaluate(document, node.left, nowTimestamp) ||
        evaluate(document, node.right, nowTimestamp)
    );
};

const UNFIELDED_HIGHLIGHT_FIELDS = [
    "short_name",
    "full_name",
    "content",
    "summary",
    "tags",
    "tika_meta.dc_creator",
];

const fieldsForHighlight = (
    document: DemoDocument,
    field: string | undefined,
): Array<[string, string[]]> => {
    const fields = textValuesByField(document);
    if (!field)
        return UNFIELDED_HIGHLIGHT_FIELDS.flatMap((name) =>
            fields[name] ? [[name, fields[name]] as [string, string[]]] : [],
        );
    const aliases = TEXT_FIELDS_BY_ALIAS[field];
    if (aliases)
        return aliases.flatMap((name) =>
            fields[name] ? [[name, fields[name]] as [string, string[]]] : [],
        );
    if (field === "*") return Object.entries(fields);
    if (!field.includes("*") && !field.includes("?"))
        return fields[field] ? [[field, fields[field]]] : [];
    return Object.entries(fields).filter(([name]) =>
        matchesWildcard(name, field, false),
    );
};

const matchingPositivePredicates = (
    document: DemoDocument,
    node: QueryNode,
    nowTimestamp: number,
): Predicate[] => {
    if (!evaluate(document, node, nowTimestamp)) return [];
    if (node.kind === "predicate") return [node];
    if (node.kind === "not") return [];
    return [
        ...matchingPositivePredicates(document, node.left, nowTimestamp),
        ...matchingPositivePredicates(document, node.right, nowTimestamp),
    ];
};

const mergeRanges = (ranges: TextRange[]): TextRange[] => {
    const sorted = ranges
        .filter((range) => range.end > range.start)
        .sort(
            (left, right) => left.start - right.start || left.end - right.end,
        );
    const merged: TextRange[] = [];
    sorted.forEach((range) => {
        const previous = merged.at(-1);
        if (!previous || range.start > previous.end) {
            merged.push({ ...range });
            return;
        }
        previous.end = Math.max(previous.end, range.end);
    });
    return merged;
};

const renderRanges = (value: string, ranges: TextRange[]): string => {
    let result = "";
    let offset = 0;
    mergeRanges(ranges).forEach((range) => {
        result += value.slice(offset, range.start);
        result += `<highlight>${value.slice(range.start, range.end)}</highlight>`;
        offset = range.end;
    });
    return result + value.slice(offset);
};

const highlightsForNode = (
    document: DemoDocument,
    node: QueryNode,
    nowTimestamp: number,
): Record<string, string[]> => {
    const matches = new Map<string, Map<string, TextRange[]>>();
    matchingPositivePredicates(document, node, nowTimestamp).forEach(
        (predicate) => {
            fieldsForHighlight(document, predicate.field).forEach(
                ([field, values]) => {
                    values.forEach((value) => {
                        const ranges = rangesForPredicate(value, predicate);
                        if (ranges.length === 0) return;
                        const valuesByRange =
                            matches.get(field) ??
                            new Map<string, TextRange[]>();
                        valuesByRange.set(value, [
                            ...(valuesByRange.get(value) ?? []),
                            ...ranges,
                        ]);
                        matches.set(field, valuesByRange);
                    });
                },
            );
        },
    );
    return Object.fromEntries(
        [...matches].map(([field, values]) => [
            field,
            [...values].map(([value, ranges]) => renderRanges(value, ranges)),
        ]),
    );
};

const referencesField = (node: QueryNode, field: string): boolean => {
    if (node.kind === "predicate") return node.field === field;
    if (node.kind === "not") return referencesField(node.operand, field);
    return (
        referencesField(node.left, field) || referencesField(node.right, field)
    );
};

export interface DemoQuery {
    highlights: (document: DemoDocument) => Record<string, string[]>;
    matches: (document: DemoDocument) => boolean;
    references: (field: string) => boolean;
}

export const parseDemoQuery = (query: string): DemoQuery => {
    if (query.length > 2_000)
        throw new DemoQueryError("Query is too long for demo mode");
    const node = new QueryParser(tokenize(query.trim())).parse();
    const nowTimestamp = Date.now();
    return {
        highlights: (document) =>
            highlightsForNode(document, node, nowTimestamp),
        matches: (document) => evaluate(document, node, nowTimestamp),
        references: (field) => referencesField(node, field),
    };
};
