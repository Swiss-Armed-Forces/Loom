import {
    setDisplayStat,
    setDisplayHistogramStat,
} from "@app/slices/searchSlice";
import type { AppDispatch } from "@app/store";

import type { PassiveFrontendTool } from "./types";

export const createSetStatisticsViewTool = (
    dispatch: AppDispatch,
): PassiveFrontendTool => ({
    interactive: false,
    definition: {
        name: "set_statistics_view",
        description:
            "Change which stat is displayed in the statistics panel. " +
            "Use this after opening the statistics tab to focus on a relevant field. " +
            "The available stat IDs come from the terms_stats and histogram_stats fields in the app state.",
        parameters: {
            type: "object",
            properties: {
                terms_stat: {
                    type: "string",
                    description:
                        "The stat ID to display in the pie chart (e.g. 'extension', 'detected_language'). " +
                        "Must be one of the IDs from the terms_stats list in the app state.",
                },
                histogram_stat: {
                    type: "string",
                    description:
                        "The stat ID to display in the histogram (e.g. 'tika_meta.dcterms_created', 'size'). " +
                        "Must be one of the IDs from the histogram_stats list in the app state.",
                },
            },
        },
    },
    handler: async (args) => {
        if ("terms_stat" in args && typeof args.terms_stat === "string") {
            dispatch(setDisplayStat(args.terms_stat));
        }
        if (
            "histogram_stat" in args &&
            typeof args.histogram_stat === "string"
        ) {
            dispatch(setDisplayHistogramStat(args.histogram_stat));
        }
        return JSON.stringify({ success: true });
    },
});
