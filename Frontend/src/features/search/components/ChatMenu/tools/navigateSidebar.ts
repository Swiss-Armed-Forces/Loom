import {
    RightSidebarTab,
    closeRightSidebar,
    setRightSidebarTab,
} from "@app/slices/searchSlice";
import type { AppDispatch } from "@app/store";

import type { PassiveFrontendTool } from "./types";

const makeOpenTabTool = (
    dispatch: AppDispatch,
    tab: RightSidebarTab,
    description: string,
): PassiveFrontendTool => ({
    interactive: false,
    definition: {
        name: `open_${tab}_sidebar`,
        description,
        parameters: { type: "object", properties: {} },
    },
    handler: async () => {
        dispatch(setRightSidebarTab(tab));
        return JSON.stringify({ success: true });
    },
});

export const createRightSidebarTools = (
    dispatch: AppDispatch,
): PassiveFrontendTool[] => [
    makeOpenTabTool(
        dispatch,
        RightSidebarTab.BULK_ACTIONS,
        "Open the bulk actions right sidebar.",
    ),
    makeOpenTabTool(
        dispatch,
        RightSidebarTab.FOLDER,
        "Open the folder right sidebar.",
    ),
    makeOpenTabTool(
        dispatch,
        RightSidebarTab.STATISTICS,
        "Open the statistics right sidebar.",
    ),
    makeOpenTabTool(
        dispatch,
        RightSidebarTab.FILE_DETAIL,
        "Open the file detail right sidebar.",
    ),
    {
        interactive: false,
        definition: {
            name: "close_sidebar",
            description: "Close the right sidebar.",
            parameters: { type: "object", properties: {} },
        },
        handler: async () => {
            dispatch(closeRightSidebar());
            return JSON.stringify({ success: true });
        },
    },
];
