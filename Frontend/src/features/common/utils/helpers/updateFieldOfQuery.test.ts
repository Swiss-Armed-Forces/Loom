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
        expect(result).toBe('tags:"ui-uploaded" *');
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
        expect(result).toBe('tags:"ui-uploaded" *');
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
        expect(result).toBe('filename:"//crawler0/test\\"folder/*" *');
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
        expect(result).toBe("filename:* *");
    });

    it("should replace unquoted wildcard with a quoted filename", () => {
        // act
        const result = updateFieldOfQuery(
            "* filename:*",
            SearchQueryField.Filename,
            "//crawler0/some/path",
        );

        // assert
        expect(result).toBe('filename:"//crawler0/some/path" *');
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
        expect(result).toBe('NOT tags:"spam" *');
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
        expect(result).toBe('NOT tags:"spam" *');
    });

    it("should replace a negated field entry with a positive one", () => {
        // act
        const result = updateFieldOfQuery(
            'NOT tags:"spam" *',
            SearchQueryField.Tags,
            "interesting",
        );

        // assert
        expect(result).toBe('tags:"interesting" *');
    });
});
