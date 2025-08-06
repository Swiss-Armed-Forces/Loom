import { describe, expect, it } from "vitest";
import {
    updateFieldOfQuery,
    updateFilenameOfQuery,
    updateTagOfQuery,
    updateWhenOfQuery,
} from "./SearchQueryUtils";

describe("SearchQueryUtils", () => {
    it("should updateTagOfQuery correctly with previous start query", () => {
        // act
        const result = updateTagOfQuery("*", "ui-uploaded");

        // assert
        expect(result).toBe('tags:"ui-uploaded" *');
    });

    it("should updateTagOfQuery correctly with empty query", () => {
        // act
        const result = updateTagOfQuery("", "ui-uploaded");

        // assert
        expect(result).toBe('tags:"ui-uploaded"');
    });

    it("should updateTagOfQuery correctly replace previous tag", () => {
        // act
        const result = updateTagOfQuery('* tags:"some-old-tag"', "ui-uploaded");

        // assert
        expect(result).toBe('tags:"ui-uploaded" *');
    });

    it("should updateTagOfQuery correctly replace previous tag with many spaces", () => {
        // act
        const result = updateTagOfQuery(
            '*  tags:"some-old-tag"  when:"yesterday"',
            "ui-uploaded",
        );

        // assert
        expect(result).toBe('tags:"ui-uploaded" * when:"yesterday"');
    });

    it("should updateWhenOfQuery correctly with previous start query", () => {
        // act
        const result = updateWhenOfQuery("*", "yesterday");

        // assert
        expect(result).toBe('when:"yesterday" *');
    });

    it("should updateWhenOfQuery correctly with empty query", () => {
        // act
        const result = updateWhenOfQuery("", "today");

        // assert
        expect(result).toBe('when:"today"');
    });

    it("should updateWhenOfQuery correctly replace previous when", () => {
        // act
        const result = updateWhenOfQuery('* when:"thisweek"', "today");

        // assert
        expect(result).toBe('when:"today" *');
    });

    it("should updateWhenOfQuery correctly replace previous when with many spaces", () => {
        // act
        const result = updateWhenOfQuery(
            '*  tags:"ui-uploaded"  when:"today"',
            "thisweek",
        );

        // assert
        expect(result).toBe('when:"thisweek" *  tags:"ui-uploaded"');
    });

    it("should updateFilenameOfQuery correctly with nested paths", () => {
        // act
        const result = updateFilenameOfQuery(
            '* filename:"*.txt"',
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
