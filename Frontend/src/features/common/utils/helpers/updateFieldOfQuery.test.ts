import { describe, expect, it } from "vitest";

import { SearchQueryField } from "@features/common/utils/enums";

import { updateFieldOfQuery } from "./updateFieldOfQuery";

describe("SearchQueryUtils", () => {
    it("should updateTagOfQuery correctly with previous start query", () => {
        // act
        const result = updateFieldOfQuery(
            "*",
            SearchQueryField.Tags,
            "ui-uploaded",
        );

        // assert
        expect(result).toBe('tags:"ui-uploaded"');
    });

    it("should updateTagOfQuery correctly with empty query", () => {
        // act
        const result = updateFieldOfQuery(
            "",
            SearchQueryField.Tags,
            "ui-uploaded",
        );

        // assert
        expect(result).toBe('tags:"ui-uploaded"');
    });

    it("should updateTagOfQuery correctly replace previous tag", () => {
        // act
        const result = updateFieldOfQuery(
            '* tags:"some-old-tag"',
            SearchQueryField.Tags,
            "ui-uploaded",
        );

        // assert
        expect(result).toBe('tags:"ui-uploaded"');
    });

    it("should updateTagOfQuery correctly replace previous tag with many spaces", () => {
        // act
        const result = updateFieldOfQuery(
            '*  tags:"some-old-tag"  when:"yesterday"',
            SearchQueryField.Tags,
            "ui-uploaded",
        );

        // assert
        expect(result).toBe('tags:"ui-uploaded" * when:"yesterday"');
    });

    it("should updateFilenameOfQuery correctly with nested paths", () => {
        // act
        const result = updateFieldOfQuery(
            '* filename:"*.txt"',
            SearchQueryField.Filename,
            '//crawler0/test"folder/*',
        );

        // assert
        expect(result).toBe('filename:"//crawler0/test\\"folder/*"');
    });

    it("should updateFieldOfQuery correctly with multiple field values", () => {
        // act
        const result = updateFieldOfQuery(
            'tags:("value1" OR "value2")',
            SearchQueryField.Extension,
            ["value3", "value4"],
        );

        // assert
        expect(result).toBe(
            'extension:("value3" OR "value4") tags:("value1" OR "value2")',
        );
    });

    it("should updateFieldOfQuery correctly with multiple field multiple values already there", () => {
        // act
        const result = updateFieldOfQuery(
            'tags:("value1" OR "value2") extension:("value3" OR "value4")',
            SearchQueryField.Extension,
            ["value5", "value6"],
        );

        // assert
        expect(result).toBe(
            'extension:("value5" OR "value6") tags:("value1" OR "value2")',
        );
    });

    it("should updateFieldOfQuery correctly with multiple field single values already there", () => {
        // act
        const result = updateFieldOfQuery(
            'tags:("value1" OR "value2") extension:"value3"',
            SearchQueryField.Extension,
            ["value4", "value5"],
        );

        // assert
        expect(result).toBe(
            'extension:("value4" OR "value5") tags:("value1" OR "value2")',
        );
    });

    it("should updateFieldOfQuery correctly with single field values already there", () => {
        // act
        const result = updateFieldOfQuery(
            'tags:("value1" OR "value2") extension:("value3" OR "value4")',
            SearchQueryField.Extension,
            "value5",
        );

        // assert
        expect(result).toBe('extension:"value5" tags:("value1" OR "value2")');
    });

    it("should throw when noQuote is true and multiple values are provided", () => {
        // assert
        expect(() =>
            updateFieldOfQuery(
                "",
                SearchQueryField.Tags,
                ["value1", "value2"],
                true,
            ),
        ).toThrow(
            "updateFieldOfQuery: noQuote does not support multiple values",
        );
    });

    it("should emit unquoted value when noQuote is true", () => {
        // act
        const result = updateFieldOfQuery(
            "",
            SearchQueryField.Filename,
            "*",
            true,
        );

        // assert
        expect(result).toBe("filename:*");
    });

    it("should replace quoted filename with unquoted wildcard", () => {
        // act
        const result = updateFieldOfQuery(
            '* filename:"//crawler0/some/path"',
            SearchQueryField.Filename,
            "*",
            true,
        );

        // assert
        expect(result).toBe("filename:*");
    });

    it("should replace unquoted wildcard with a quoted filename", () => {
        // act
        const result = updateFieldOfQuery(
            "* filename:*",
            SearchQueryField.Filename,
            "//crawler0/some/path",
        );

        // assert
        expect(result).toBe('filename:"//crawler0/some/path"');
    });

    it("should replace unquoted wildcard with another unquoted wildcard", () => {
        // act
        const result = updateFieldOfQuery(
            "filename:*",
            SearchQueryField.Filename,
            "*",
            true,
        );

        // assert
        expect(result).toBe("filename:*");
    });

    it("should negate a field entry when negate is true", () => {
        // act
        const result = updateFieldOfQuery(
            "*",
            SearchQueryField.Tags,
            "spam",
            false,
            true,
        );

        // assert
        expect(result).toBe('NOT tags:"spam"');
    });

    it("should replace a positive field entry with a negated one", () => {
        // act
        const result = updateFieldOfQuery(
            'tags:"old-tag" *',
            SearchQueryField.Tags,
            "spam",
            false,
            true,
        );

        // assert
        expect(result).toBe('NOT tags:"spam"');
    });

    it("should replace a negated field entry with a positive one", () => {
        // act
        const result = updateFieldOfQuery(
            'NOT tags:"spam" *',
            SearchQueryField.Tags,
            "interesting",
        );

        // assert
        expect(result).toBe('tags:"interesting"');
    });

    it("should replace a closed Lucene range with a new range value", () => {
        // act
        const result = updateFieldOfQuery(
            "uploaded_datetime:[2020-01-01 TO 2021-01-01] *",
            "uploaded_datetime",
            "[2022-01-01 TO 2023-01-01]",
            true,
        );

        // assert
        expect(result).toBe("uploaded_datetime:[2022-01-01 TO 2023-01-01]");
    });

    it("should replace a half-open Lucene range with a new value", () => {
        // act
        const result = updateFieldOfQuery(
            "uploaded_datetime:[2020-01-01 TO 2021-01-01} *",
            "uploaded_datetime",
            "[2022-01-01 TO 2023-01-01}",
            true,
        );

        // assert
        expect(result).toBe("uploaded_datetime:[2022-01-01 TO 2023-01-01}");
    });

    it("should remove a range field when given an empty array", () => {
        // act
        const result = updateFieldOfQuery(
            "uploaded_datetime:[2020-01-01 TO 2021-01-01] *",
            "uploaded_datetime",
            [],
        );

        // assert
        expect(result).toBe("");
    });

    it("should not match range syntax as part of a regular quoted value", () => {
        // act - quoted value containing bracket chars should not be double-removed
        const result = updateFieldOfQuery(
            'tags:"value1" *',
            SearchQueryField.Tags,
            "value2",
        );

        // assert
        expect(result).toBe('tags:"value2"');
    });

    it("should extend an existing NOT filter when negating again (single existing value)", () => {
        const result = updateFieldOfQuery(
            'NOT tags:"spam"',
            SearchQueryField.Tags,
            "more-spam",
            false,
            true,
        );

        expect(result).toBe('NOT tags:("spam" OR "more-spam")');
    });

    it("should extend an existing NOT filter when negating again (multiple existing values)", () => {
        const result = updateFieldOfQuery(
            'NOT extension:("pdf" OR "docx")',
            SearchQueryField.Extension,
            ["txt", "xlsx"],
            false,
            true,
        );

        expect(result).toBe(
            'NOT extension:("pdf" OR "docx" OR "txt" OR "xlsx")',
        );
    });

    it("should deduplicate when extending an existing NOT filter", () => {
        const result = updateFieldOfQuery(
            'NOT extension:("pdf" OR "docx")',
            SearchQueryField.Extension,
            ["docx", "txt"],
            false,
            true,
        );

        expect(result).toBe('NOT extension:("pdf" OR "docx" OR "txt")');
    });

    it("should not extend when switching from NOT to positive filter", () => {
        const result = updateFieldOfQuery(
            'NOT extension:("pdf" OR "docx")',
            SearchQueryField.Extension,
            "txt",
            false,
            false,
        );

        expect(result).toBe('extension:"txt"');
    });
});
