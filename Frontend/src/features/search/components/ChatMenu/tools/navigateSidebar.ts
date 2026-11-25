import { CapabilityId } from "@app/api/generated";
import {
    RightSidebarTab,
    closeRightSidebar,
    setRightSidebarTab,
} from "@app/slices/searchSlice";
import type { AppDispatch } from "@app/store";

import { toolError, toolSuccess, type PassiveFrontendTool } from "./types";

/**
 * The tabs the agent may open, and what each one shows.
 *
 * `RightSidebarTab.CHAT` is absent: it is the panel the agent is talking from.
 */
const OPENABLE_TABS: Record<string, string> = {
    [RightSidebarTab.BULK_ACTIONS]: "bulk actions over the current query",
    [RightSidebarTab.FOLDER]: "the folder tree scoped to the current query",
    [RightSidebarTab.STATISTICS]: "statistics over the current query",
    [RightSidebarTab.FILE_DETAIL]: "the detail view of the opened files",
};

const isOpenableTab = (tab: string): tab is RightSidebarTab =>
    Object.hasOwn(OPENABLE_TABS, tab);

const describeTabs = () =>
    Object.entries(OPENABLE_TABS)
        .map(([tab, shows]) => `'${tab}' (${shows})`)
        .join(", ");

export const createRightSidebarTools = (
    dispatch: AppDispatch,
): PassiveFrontendTool[] => [
    {
        interactive: false,
        definition: {
            name: "open_sidebar",
            capabilities: [CapabilityId.UiInteraction],
            description: `Open a tab of the right sidebar: ${describeTabs()}.`,
            parameters: {
                type: "object",
                properties: {
                    tab: {
                        type: "string",
                        enum: Object.keys(OPENABLE_TABS),
                        description: "Which sidebar tab to open.",
                    },
                },
                required: ["tab"],
            },
        },
        handler: async (args) => {
            const tab = String(args.tab ?? "");
            // An unknown tab is reported rather than dropped: dispatching nothing and
            // answering success would leave the agent believing the panel is open.
            if (!isOpenableTab(tab)) {
                return toolError(
                    `Unknown sidebar tab '${tab}'. Valid tabs are: ${Object.keys(
                        OPENABLE_TABS,
                    ).join(", ")}.`,
                );
            }
            dispatch(setRightSidebarTab(tab));
            return toolSuccess();
        },
    },
    {
        interactive: false,
        definition: {
            name: "close_sidebar",
            capabilities: [CapabilityId.UiInteraction],
            description: "Close the right sidebar.",
            parameters: { type: "object", properties: {} },
        },
        handler: async () => {
            dispatch(closeRightSidebar());
            return toolSuccess();
        },
    },
];
