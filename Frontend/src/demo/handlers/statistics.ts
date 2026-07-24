import type {
    AvailableStat,
    GroupedHistogramStatisticsModel,
    TermsStatisticsModel,
} from "@app/api/generated";

import { valuesForField } from "../query";
import type { DemoDocument } from "../repository";

export const AVAILABLE_TERMS_STATS: AvailableStat[] = [
    { id: "extension", label: "Extension" },
    { id: "tags", label: "Tags" },
    { id: "state", label: "State" },
    { id: "detected_language", label: "Detected language" },
];

export const AVAILABLE_HISTOGRAM_STATS: AvailableStat[] = [
    { id: "tika_meta.dcterms_created", label: "Created" },
    { id: "uploaded_datetime", label: "Uploaded" },
    { id: "size", label: "Size" },
];

const histogramValue = (document: DemoDocument, stat: string): number => {
    if (stat === "size") return document.size;
    return Date.parse(valuesForField(document, stat)[0] ?? "");
};

const bucketName = (value: number, stat: string): string =>
    stat === "size"
        ? String(value)
        : new Date(value).toISOString().slice(0, 10) + "T00:00:00.000Z";

const countValues = (values: string[]): Record<string, number> => {
    const result: Record<string, number> = {};
    values.forEach((value) => {
        result[value] = (result[value] ?? 0) + 1;
    });
    return result;
};

export const termsStatistics = (
    documents: DemoDocument[],
    stat: string,
    size: number,
): TermsStatisticsModel => {
    const counts = countValues(
        documents.flatMap((document) => valuesForField(document, stat)),
    );
    return {
        stat,
        key: stat,
        data: Object.entries(counts)
            .sort(
                ([leftName, leftCount], [rightName, rightCount]) =>
                    rightCount - leftCount || leftName.localeCompare(rightName),
            )
            .slice(0, size)
            .map(([name, hits]) => ({ name, hitsCount: hits })),
        fileCount: documents.length,
    };
};

export const groupedHistogramStatistics = (
    documents: DemoDocument[],
    stat: string,
    groupBy: string,
): GroupedHistogramStatisticsModel => {
    const values = documents.map((document) => histogramValue(document, stat));
    const buckets = new Map<number, DemoDocument[]>();
    documents.forEach((document) => {
        const value = histogramValue(document, stat);
        const bucket = buckets.get(value) ?? [];
        bucket.push(document);
        buckets.set(value, bucket);
    });
    return {
        stat,
        groupBy,
        key: stat,
        histogramType: stat === "size" ? "number" : "date",
        data: [...buckets.entries()]
            .sort(([left], [right]) => left - right)
            .map(([value, bucketDocuments]) => ({
                name: bucketName(value, stat),
                groups: countValues(
                    bucketDocuments.flatMap((document) =>
                        valuesForField(document, groupBy),
                    ),
                ),
                hitsCount: bucketDocuments.length,
            })),
        fileCount: documents.length,
        minValue: values.length > 0 ? Math.min(...values) : undefined,
        maxValue: values.length > 0 ? Math.max(...values) : undefined,
    };
};
