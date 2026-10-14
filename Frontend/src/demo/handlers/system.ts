import { http, HttpResponse } from "msw";

import {
    AboutInfoToJSON,
    CompleteEstimateResultToJSON,
    QueuesStatsToJSON,
} from "@app/api/generated";

import { DemoQueryError } from "../query";
import {
    type DemoTask,
    getMetrics,
    scheduleTask,
    searchDocuments,
} from "../repository";

import {
    empty,
    error,
    json,
    objectValue,
    parseBody,
    stringValue,
} from "./shared";

const summarizationPromptHandler = http.get(
    /\/api\/v1\/files\/summarization\/system_prompt$/,
    () => new HttpResponse("Summarize the document accurately and concisely."),
);

const imageDescriptionPromptHandler = http.get(
    /\/api\/v1\/files\/image_description\/system_prompt$/,
    () => new HttpResponse("Describe the image and extract useful details."),
);

const bulkTaskHandler = http.post(
    /\/api\/v1\/files\/(summarization|image_description|index|translation)$/,
    async ({ request }) => {
        const parsed = await parseBody(request);
        if (!parsed.ok) return parsed.response;
        const query = objectValue(parsed.value.query);
        if (!query || typeof query.search_string !== "string")
            return error("query.search_string is required", 422);

        const operation = new URL(request.url).pathname.match(
            /\/files\/(summarization|image_description|index|translation)$/,
        )?.[1];
        let task: DemoTask;
        if (operation === "translation") {
            const language = stringValue(parsed.value.lang)?.trim();
            if (!language) return error("lang is required", 422);
            task = { kind: "translate", language };
        } else if (operation === "summarization") {
            task = { kind: "summarize" };
        } else if (operation === "image_description") {
            task = { kind: "image_description" };
        } else {
            task = { kind: "index" };
        }

        try {
            searchDocuments(query.search_string).forEach((document) =>
                scheduleTask(document.id, task),
            );
        } catch (reason) {
            return error(
                reason instanceof DemoQueryError
                    ? reason.message
                    : "Invalid task query",
                400,
            );
        }
        return empty(202);
    },
);

const queuesHandler = http.get(/\/api\/v1\/queues\/stats$/, () => {
    const metrics = getMetrics();
    return json(
        QueuesStatsToJSON({
            messagesInQueues: metrics.messagesInQueues,
            pausedQueues: [],
        }),
    );
});

const estimateHandler = http.get(/\/api\/v1\/complete-estimate$/, () => {
    const metrics = getMetrics();
    return json(
        CompleteEstimateResultToJSON({
            estimateTimestamp: metrics.estimateTimestamp,
            filesPending: metrics.filesPending,
        }),
    );
});

// The demo runs no chart, so there is no release to report. "demo" is a literal
// rather than a copied version number on purpose: a number here would be wrong
// the moment the chart moves, which is the duplication /v1/about exists to end.
const aboutHandler = http.get(/\/api\/v1\/about$/, () =>
    json(
        AboutInfoToJSON({
            name: "loom",
            version: "demo",
            appVersion: "demo",
            description:
                "Loom is a powerful and easily deployable open-source document search engine.",
        }),
    ),
);

const metricsHandler = http.get(
    /\/api\/v1\/metrics$/,
    () =>
        new HttpResponse("loom_demo_healthy 1\nloom_demo_documents 5\n", {
            headers: { "Content-Type": "text/plain" },
        }),
);

export const systemHandlers = [
    summarizationPromptHandler,
    imageDescriptionPromptHandler,
    bulkTaskHandler,
    queuesHandler,
    estimateHandler,
    aboutHandler,
    metricsHandler,
];
