import { describe, expect, it } from "vitest";
import {
    updateFilenameOfQuery,
    updateTagOfQuery,
    updateWhenOfQuery,
} from "./SearchQueryUtils";

describe("SearchQueryUtils", () => {
    it("should updateTagOfQuery correctly with previous start query", () => {
        // act
        const result = updateTagOfQuery("*", "ui-uploaded");

        // assert
        expect(result).toBe('* tags:"ui-uploaded"');
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
        expect(result).toBe('* tags:"ui-uploaded"');
    });

    it("should updateTagOfQuery correctly replace previous tag with many spaces", () => {
        // act
        const result = updateTagOfQuery(
            '*  tags:"some-old-tag"  when:"yesterday"',
            "ui-uploaded",
        );

        // assert
        expect(result).toBe('*    when:"yesterday" tags:"ui-uploaded"');
    });

    it("should updateWhenOfQuery correctly with previous start query", () => {
        // act
        const result = updateWhenOfQuery("*", "yesterday");

        // assert
        expect(result).toBe('* when:"yesterday"');
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
        expect(result).toBe('* when:"today"');
    });

    it("should updateWhenOfQuery correctly replace previous when with many spaces", () => {
        // act
        const result = updateWhenOfQuery(
            '*  tags:"ui-uploaded"  when:"today"',
            "thisweek",
        );

        // assert
        expect(result).toBe('*  tags:"ui-uploaded" when:"thisweek"');
    });

    it("should updateFilenameOfQuery currectly with nested paths", () => {
        // act
        const result = updateFilenameOfQuery(
            '* filename:"*.txt"',
            '//crawler0/test"folder/*',
        );

        // assert
        expect(result).toBe('* filename:"//crawler0/test\\"folder/*"');
    });
});
