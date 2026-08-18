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

    it("should accumulate into an empty query (behaves like a normal click)", () => {
        const result = updateFieldOfQuery(
            "",
            SearchQueryField.Tags,
            "new-tag",
            false,
            false,
            true,
        );

        expect(result).toBe('tags:"new-tag"');
    });

    it("should accumulate a new value into an existing single positive filter", () => {
        const result = updateFieldOfQuery(
            'tags:"existing"',
            SearchQueryField.Tags,
            "new-tag",
            false,
            false,
            true,
        );

        expect(result).toBe('tags:("existing" OR "new-tag")');
    });

    it("should accumulate a new value into an existing multi-value positive filter", () => {
        const result = updateFieldOfQuery(
            'tags:("a" OR "b")',
            SearchQueryField.Tags,
            "c",
            false,
            false,
            true,
        );

        expect(result).toBe('tags:("a" OR "b" OR "c")');
    });

    it("should deduplicate when accumulating the same value again", () => {
        const result = updateFieldOfQuery(
            'tags:("a" OR "b")',
            SearchQueryField.Tags,
            "a",
            false,
            false,
            true,
        );

        expect(result).toBe('tags:("a" OR "b")');
    });

    it("should ignore accumulate when noQuote is true", () => {
        // accumulate=true is ignored when noQuote=true; quoted value is
        // replaced by the new unquoted wildcard (no OR merge).
        const result = updateFieldOfQuery(
            'filename:"//crawler0/some/path"',
            SearchQueryField.Filename,
            "*",
            true,
            false,
            true,
        );

        expect(result).toBe("filename:*");
    });

    it("should ignore accumulate when negate is true", () => {
        // accumulate=true is ignored when negate=true; the existing positive
        // filter is replaced by a negated one (no OR merge).
        const result = updateFieldOfQuery(
            'tags:"existing"',
            SearchQueryField.Tags,
            "new-tag",
            false,
            true,
            true,
        );

        expect(result).toBe('NOT tags:"new-tag"');
    });

    describe("clearFields", () => {
        it("should strip specified fields when clearFields is provided", () => {
            const result = updateFieldOfQuery(
                'parent_path:"a/b"',
                SearchQueryField.FullPathTree,
                "a/b",
                false,
                false,
                false,
                [SearchQueryField.ParentPath],
            );

            expect(result).toBe('full_path.tree:"a/b"');
        });

        it("should strip existing FullPathTree when clearFields includes it", () => {
            const result = updateFieldOfQuery(
                'full_path.tree:"a/b"',
                SearchQueryField.ParentPath,
                "a/b",
                false,
                false,
                false,
                [SearchQueryField.FullPathTree],
            );

            expect(result).toBe('parent_path:"a/b"');
        });

        it("should strip clearFields while preserving unrelated fields", () => {
            const result = updateFieldOfQuery(
                'parent_path:"a" tags:"foo"',
                SearchQueryField.FullPathTree,
                "a",
                false,
                false,
                false,
                [SearchQueryField.ParentPath],
            );

            expect(result).toBe('full_path.tree:"a" tags:"foo"');
        });

        it("should strip negated clearFields", () => {
            const result = updateFieldOfQuery(
                'NOT parent_path:"x"',
                SearchQueryField.FullPathTree,
                "y",
                false,
                false,
                false,
                [SearchQueryField.ParentPath],
            );

            expect(result).toBe('full_path.tree:"y"');
        });

        it("should leave other fields untouched when no clearFields is provided", () => {
            const result = updateFieldOfQuery(
                'parent_path:"a" tags:"foo"',
                SearchQueryField.Tags,
                "bar",
            );

            expect(result).toBe('tags:"bar" parent_path:"a"');
        });

        it("should strip Seen and Flagged when listed in clearFields", () => {
            const result = updateFieldOfQuery(
                'full_path.tree:"/old" seen:"false" tags:"foo"',
                SearchQueryField.FullPathTree,
                "/new",
                false,
                false,
                false,
                [SearchQueryField.Seen, SearchQueryField.Flagged],
            );

            expect(result).toBe('full_path.tree:"/new" tags:"foo"');
        });

        it("should strip multiple clearFields at once", () => {
            const result = updateFieldOfQuery(
                'full_path.tree:"/a" flagged:"true"',
                SearchQueryField.ParentPath,
                "/a",
                false,
                false,
                false,
                [SearchQueryField.FullPathTree, SearchQueryField.Flagged],
            );

            expect(result).toBe('parent_path:"/a"');
        });

        it("should strip Flagged when Seen is set with clearFields", () => {
            const result = updateFieldOfQuery(
                'flagged:"true"',
                SearchQueryField.Seen,
                "false",
                false,
                false,
                false,
                [SearchQueryField.Flagged],
            );

            expect(result).toBe('seen:"false"');
        });

        it("should not strip fields not listed in clearFields", () => {
            const result = updateFieldOfQuery(
                'full_path.tree:"/a"',
                SearchQueryField.FullPathKeyword,
                "/a",
                false,
                true,
            );

            expect(result).toBe(
                'NOT full_path.keyword:"/a" full_path.tree:"/a"',
            );
        });

        it("should build a complete subtree exclusion query step by step", () => {
            // Simulates what subtreeBaseQuery + handleFlaggedClick does:
            // 1. Set FullPathTree, clearing Seen, Flagged, ParentPath, FullPathKeyword
            let query = updateFieldOfQuery(
                'parent_path:"/old" seen:"false"',
                SearchQueryField.FullPathTree,
                "/a",
                false,
                false,
                false,
                [
                    SearchQueryField.ParentPath,
                    SearchQueryField.FullPathKeyword,
                    SearchQueryField.Seen,
                    SearchQueryField.Flagged,
                ],
            );
            // 2. Set NOT FullPathKeyword, clearing only ParentPath
            query = updateFieldOfQuery(
                query,
                SearchQueryField.FullPathKeyword,
                "/a",
                false,
                true,
                false,
                [SearchQueryField.ParentPath],
            );
            // 3. Set Flagged, clearing only Seen
            query = updateFieldOfQuery(
                query,
                SearchQueryField.Flagged,
                "true",
                false,
                false,
                false,
                [SearchQueryField.Seen],
            );

            expect(query).toBe(
                'flagged:"true" NOT full_path.keyword:"/a" full_path.tree:"/a"',
            );
        });
    });
});
