import type { AppDispatch } from "@app/store";

import { createAskUserTool } from "./askUser";
import { createCloseFileTool } from "./closeFileTab";
import { createDiscoverStateTool } from "./discoverState";
import { createGetTheseFilesTool } from "./getTheseFiles";
import { createGetThisFileTool } from "./getThisFile";
import { createHighlightFileTool } from "./highlightFile";
import { createRightSidebarTools } from "./navigateSidebar";
import { createNavigateToFileTool } from "./navigateToFile";
import { createOpenFileDialogTools } from "./openFileDialogs";
import { createReadStateTool } from "./readState";
import { createRequestModeTool } from "./requestMode";
import { createSaveCustomQueryTool } from "./saveCustomQuery";
import { createSetSearchQueryTool } from "./setSearchQuery";
import { createSetStatisticsViewTool } from "./setStatisticsView";
import type { FrontendToolRegistry, StateAccessor } from "./types";

export type {
    FrontendTool,
    FrontendToolRegistry,
    StateAccessor,
} from "./types";

export const createFrontendTools = (
    getState: StateAccessor,
    dispatch: AppDispatch,
): FrontendToolRegistry => {
    const tools = [
        createDiscoverStateTool(),
        createReadStateTool(getState),
        createAskUserTool(),
        createRequestModeTool(),
        createGetThisFileTool(getState),
        createGetTheseFilesTool(getState),
        createSetSearchQueryTool(getState, dispatch),
        createNavigateToFileTool(dispatch),
        createHighlightFileTool(dispatch),
        ...createRightSidebarTools(dispatch),
        createSaveCustomQueryTool(getState, dispatch),
        ...createOpenFileDialogTools(getState, dispatch),
        createSetStatisticsViewTool(dispatch),
        createCloseFileTool(dispatch),
    ];
    const registry: FrontendToolRegistry = {};
    for (const tool of tools) {
        registry[tool.definition.name] = tool;
    }
    return registry;
};
