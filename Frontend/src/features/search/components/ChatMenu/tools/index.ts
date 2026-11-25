import type { AppDispatch } from "@app/store";

import { createAskUserTool } from "./askUser";
import { createDiscoverStateTool } from "./discoverState";
import { createGetHighlightedFileTool } from "./getHighlightedFile";
import { createRightSidebarTools } from "./navigateSidebar";
import { createReadStateTool } from "./readState";
import { createRequestModeTool } from "./requestMode";
import { createSaveCustomQueryTool } from "./saveCustomQuery";
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
        createGetHighlightedFileTool(getState),
        ...createRightSidebarTools(dispatch),
        createSaveCustomQueryTool(getState, dispatch),
        createSetStatisticsViewTool(dispatch),
    ];
    const registry: FrontendToolRegistry = {};
    for (const tool of tools) {
        registry[tool.definition.name] = tool;
    }
    return registry;
};
