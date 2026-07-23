export interface SearchTip {
    query: string;
    translationKey: string;
}

export const SEARCH_TIPS: SearchTip[] = [
    { query: "*", translationKey: "showAll" },
    { query: "John Smith", translationKey: "keyword" },
    { query: "Jo*", translationKey: "prefix" },
    { query: "/.*Jo?n.*/", translationKey: "regex" },
    { query: '"John Smith"', translationKey: "exact" },
    { query: '"John Smith"~10', translationKey: "exactDistance" },
    { query: "John~2", translationKey: "fuzzy" },
    { query: "filename:*.txt", translationKey: "filename" },
    { query: "size:>1M", translationKey: "size" },
    { query: "modified:today", translationKey: "when" },
    { query: "author:/.*/", translationKey: "author" },
    { query: "tags:interesting", translationKey: "tags" },
    { query: "NOT tags:interesting", translationKey: "tagsNegate" },
    {
        query: "tags:interesting AND modified:today",
        translationKey: "and",
    },
    {
        query: "tags:interesting OR modified:today",
        translationKey: "or",
    },
    { query: "seen:true", translationKey: "seen" },
    { query: "flagged:true", translationKey: "flagged" },
    { query: "hidden:true", translationKey: "hidden" },
    { query: "hidden:*", translationKey: "allHidden" },
    { query: 'file_type:"image/png"', translationKey: "fileType" },
    {
        query: "uploaded:[* TO 2020-06-15]",
        translationKey: "uploadTime",
    },
    {
        query: "created:{2020-12-31 TO 2025-01-01}",
        translationKey: "creationTime",
    },
    {
        query: "modified:[2021-01-01 TO 2025-01-01}",
        translationKey: "modificationTime",
    },
    { query: "secrets:*", translationKey: "secrets" },
    { query: "source:crawlerX", translationKey: "source" },
    { query: "state:failed", translationKey: "stateFailed" },
    { query: "summary:*", translationKey: "summary" },
    { query: "*:John", translationKey: "allFields" },
    { query: "\\*name\\*:*txt*", translationKey: "nameFields" },
];
