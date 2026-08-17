import type { AppDispatch } from "@app/store";

import { createAddTagsToFileTool } from "./addTagsToFile";
import { createAskUserTool } from "./askUser";
import { createDiscoverStateTool } from "./discoverState";
import { createGetTheseFilesTool } from "./getTheseFiles";
import { createGetThisFileTool } from "./getThisFile";
import { createHighlightFileTool } from "./highlightFile";
import { createRightSidebarTools } from "./navigateSidebar";
import { createNavigateToFileTool } from "./navigateToFile";
import { createOpenFileDialogTools } from "./openFileDialogs";
import { createReadStateTool } from "./readState";
import { createRequestCapabilityTool } from "./requestCapability";
import { createSaveCustomQueryTool } from "./saveCustomQuery";
import { createSetSearchQueryTool } from "./setSearchQuery";
import { createSetStatisticsViewTool } from "./setStatisticsView";
import type { FrontendToolRegistry, StateAccessor } from "./types";
import { createUpdateFileFlagsTool } from "./updateFileFlags";

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
        createRequestCapabilityTool(),
        createGetThisFileTool(getState),
        createGetTheseFilesTool(getState),
        createSetSearchQueryTool(getState, dispatch),
        createNavigateToFileTool(dispatch),
        createHighlightFileTool(dispatch),
        ...createRightSidebarTools(dispatch),
        createSaveCustomQueryTool(getState, dispatch),
        ...createOpenFileDialogTools(getState, dispatch),
        createUpdateFileFlagsTool(getState, dispatch),
        createAddTagsToFileTool(getState, dispatch),
        createSetStatisticsViewTool(dispatch),
    ];
    const registry: FrontendToolRegistry = {};
    for (const tool of tools) {
        registry[tool.definition.name] = tool;
    }
    return registry;
};
