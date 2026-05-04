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
        const result = updateFieldOfQuery('abc:("value1 OR "value2")', "def", [
            "value3",
            "value4",
        ]);

        // assert
        expect(result).toBe(
            'def:("value3" OR "value4") abc:("value1 OR "value2")',
        );
    });

    it("should updateFieldOfQuery correctly with multiple field multiple values already there", () => {
        // act
        const result = updateFieldOfQuery(
            'abc:("value1 OR "value2") def:("value3" OR "value4")',
            "def",
            ["value5", "value6"],
        );

        // assert
        expect(result).toBe(
            'def:("value5" OR "value6") abc:("value1 OR "value2")',
        );
    });

    it("should updateFieldOfQuery correctly with multiple field single values already there", () => {
        // act
        const result = updateFieldOfQuery(
            'abc:("value1 OR "value2") def:"value3"',
            "def",
            ["value4", "value5"],
        );

        // assert
        expect(result).toBe(
            'def:("value4" OR "value5") abc:("value1 OR "value2")',
        );
    });

    it("should updateFieldOfQuery correctly with single field values already there", () => {
        // act
        const result = updateFieldOfQuery(
            'abc:("value1 OR "value2") def:("value3" OR "value4")',
            "def",
            "value5",
        );

        // assert
        expect(result).toBe('def:"value5" abc:("value1 OR "value2")');
    });
});
