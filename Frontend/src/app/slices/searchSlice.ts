import {
    AsyncThunkConfig,
    createAsyncThunk,
    createSelector,
    createSlice,
    GetThunkAPI,
    PayloadAction,
} from "@reduxjs/toolkit";
import { t } from "i18next";
import { toast } from "react-toastify";
import { v4 as uuidv4 } from "uuid";

import {
    getFilePreview,
    GetFilePreviewResponse,
    GetFilesFileEntry,
    searchFiles,
    GroupedHistogramStatisticsModel,
    TermsStatisticsModel,
    AvailableStat,
    PubSubMessage,
    getLongRunningQuery,
    getFilesCount,
    ResponseError,
    PreviewField,
} from "@app/api/index";
import {} from "@app/channelSubscriptions";
import {
    startLoadingIndicator,
    stopLoadingIndicator,
} from "@app/slices/commonSlice";
import {
    FileDetailSelection,
    FOLLOW_TAB,
    fileTab,
    selectedFileIdOf,
} from "@app/slices/fileDetailSelection";
import { isPreviewFresh, SearchFileEntry } from "@app/slices/searchFileEntry";
import { FileDetailTab } from "@features/common/utils/enums";
import { clamp } from "@features/common/utils/helpers";
import {
    CombinedStats,
    PitBoundSearchQuery,
    SearchQuery,
} from "@features/common/utils/model";
import { apiPreviewFields } from "@features/search/components/FieldList/indicatorFields";
import {
    clampSidebarWidth,
    DEFAULT_LEFT_SIDEBAR_WIDTH,
    DEFAULT_RIGHT_SIDEBAR_WIDTH,
} from "@features/search/components/sidebarWidth";
import { shortcutRegistry } from "@features/search/hooks/shortcutRegistry";
import {
    DEFAULT_HISTOGRAM_STAT,
    DEFAULT_TERMS_STAT,
} from "@features/search/views/Statistics/statOrder";
import { webSocketSendMessage } from "@middleware/SocketMiddleware";

import { RootState } from "../store";

export const LeftSidebarPanel = {
    FOLDER: "folder",
    TAGS: "tags",
    QUERIES: "queries",
    CUSTOMIZATION: "customization",
    CHAT: "chat",
} as const;

export type LeftSidebarPanel =
    (typeof LeftSidebarPanel)[keyof typeof LeftSidebarPanel];

export const RightSidebarTab = {
    BULK_ACTIONS: "bulk_actions",
    FOLDER: "folder_scoped",
    STATISTICS: "statistics",
    CHAT: "chat",
    FILE_DETAIL: "file_detail",
} as const;

export type RightSidebarTab =
    (typeof RightSidebarTab)[keyof typeof RightSidebarTab];

/**
 * A shortcut to a whole set of card elements; see `CARD_PRESETS`.
 *
 * A card is laid out tight and only that way, so a preset says how much of a
 * file a card shows and nothing about how much room it takes.
 */
export type CardPreset = "compact" | "standard" | "full";

/** How a single metadata field is rendered on a card.
 *  "compact" → one `label: value` line per field, with an accordion kept for
 *  truncated values only; "line" → every selected field side by side on one
 *  line, values only, the way a mail client lays a message list out. */
export type FieldLayout = "compact" | "line";

/**
 * Width of the thumbnail column on a card, in rem. Zero draws none.
 *
 * A width rather than a few named sizes: how much of a card a picture should
 * take depends on the pictures, and the reader is the one looking at them.
 * `THUMBNAIL_WIDTH_STEP_REM` is the slider's step, and is coarse on purpose -
 * the difference between neighbouring stops has to be one a reader can see.
 */
export const THUMBNAIL_WIDTH_MAX_REM = 35;
export const THUMBNAIL_WIDTH_STEP_REM = 7;

/** Most columns a card's fields may be laid out in. Past this a column is
 *  too narrow to hold a value worth reading. */
export const MAX_FIELD_COLUMNS = 4;

/** Hard ceiling on a stored depth limit.
 *
 *  Each control's real top is how deep the indexed data goes, which only the
 *  backend knows and which the slider is drawn from. This is only here to keep
 *  a stale or hand-edited localStorage value within something sane. */
const FOLDER_VIEW_DEPTH_CEILING = 64;

/** The two depth limits of one folder-view instance; `null` means no limit.
 *
 *  `pathDepth` counts path segments. `extractionDepth` counts container hops -
 *  how far inside attachments and archives to look - so 0 hides everything
 *  extracted from a file and 1 keeps an email's own attachments but not the
 *  contents of an archive attached to it. */
export interface FolderViewOptions {
    pathDepth: number | null;
    extractionDepth: number | null;
}

export const NO_FOLDER_VIEW_LIMITS: FolderViewOptions = {
    pathDepth: null,
    extractionDepth: null,
};

/** Clamp a limit into the range its control offers.
 *
 *  Persisted state is rehydrated without validation, so a hand-edited or stale
 *  localStorage blob would otherwise reach the store carrying a depth no button
 *  can display and no tree can satisfy. */
const clampDepth = (value: number | null | undefined): number | null => {
    if (typeof value !== "number" || Number.isNaN(value)) return null;
    return clamp(Math.trunc(value), 0, FOLDER_VIEW_DEPTH_CEILING);
};

export const normalizeFolderViewOptions = (
    options: Partial<FolderViewOptions> | null | undefined,
): FolderViewOptions => ({
    pathDepth: clampDepth(options?.pathDepth),
    extractionDepth: clampDepth(options?.extractionDepth),
});

// All card-element visibility settings in one shape, shared by presets and state.
export interface CardVisibilitySettings {
    thumbnailWidthRem: number;
    showHighlights: boolean;
    showExtensionIcon: boolean;
    showFilePath: boolean;
    showParentNavigation: boolean;
    showStatusIndicators: boolean;
    showAttachments: boolean;
    showTags: boolean;
    showActions: boolean;
    showSortIndicator: boolean;
    showFieldActions: boolean;
}

export const CARD_PRESETS: Record<CardPreset, CardVisibilitySettings> = {
    compact: {
        thumbnailWidthRem: 0,
        showHighlights: false,
        showExtensionIcon: true,
        showFilePath: true,
        showParentNavigation: false,
        showStatusIndicators: false,
        showAttachments: false,
        showTags: false,
        showActions: false,
        showSortIndicator: false,
        showFieldActions: false,
    },
    standard: {
        thumbnailWidthRem: 14,
        showHighlights: true,
        showExtensionIcon: true,
        showFilePath: true,
        showParentNavigation: true,
        showStatusIndicators: true,
        showAttachments: true,
        showTags: true,
        showActions: false,
        showSortIndicator: false,
        showFieldActions: false,
    },
    full: {
        thumbnailWidthRem: 21,
        showHighlights: true,
        showExtensionIcon: true,
        showFilePath: true,
        showParentNavigation: true,
        showStatusIndicators: true,
        showAttachments: true,
        showTags: true,
        showActions: true,
        showSortIndicator: true,
        showFieldActions: true,
    },
};

/** The flags a preset sets, named once so state and preset can be compared
 *  without listing them again. */
export const CARD_VISIBILITY_KEYS = Object.keys(
    CARD_PRESETS.standard,
) as (keyof CardVisibilitySettings)[];

const matchesPreset = (
    visibility: CardVisibilitySettings,
    preset: CardVisibilitySettings,
): boolean =>
    CARD_VISIBILITY_KEYS.every((key) => visibility[key] === preset[key]);

/** One tab the reader opened: a file, and the sub-tab it was left on. */
export interface OpenFileTab {
    fileId: string;
    detailTab: FileDetailTab;
}

export interface CustomQuery {
    id: string;
    query: SearchQuery;
    fileCount: number;
    // Baseline the "new files" badge compares against. It only ever moves when
    // the user opens the query (markCustomQueryAsRead); a poll reporting a
    // *lower* count must not move it, or deleting files silently rebaselines
    // and hides subsequent genuine matches.
    lastSeenCount: number;
    hasNewFiles: boolean;
    name: string;
    icon: string;
}

export const initCustomQuery = (
    query: SearchQuery,
    fileCount: number,
    name: string,
    icon: string,
): CustomQuery => {
    return {
        id: uuidv4(),
        query,
        fileCount,
        lastSeenCount: fileCount,
        hasNewFiles: false,
        name,
        icon,
    };
};

/**
 * Coerce persisted saved queries back into the current shape.
 *
 * `loadPersistedSearchState` is a bare `JSON.parse` cast, so entries written
 * before `lastSeenCount` existed arrive without it. Seeding the baseline from
 * `fileCount` is what stops every existing browser lighting up every badge on
 * the first load after deploy.
 */
export const normalizeCustomQueries = (raw: unknown): CustomQuery[] => {
    if (!Array.isArray(raw)) return [];
    return raw.flatMap((entry): CustomQuery[] => {
        if (entry === null || typeof entry !== "object") return [];
        const candidate = entry as Partial<CustomQuery>;
        if (
            typeof candidate.id !== "string" ||
            typeof candidate.name !== "string" ||
            candidate.query === null ||
            typeof candidate.query !== "object"
        ) {
            return [];
        }
        const fileCount =
            typeof candidate.fileCount === "number" ? candidate.fileCount : 0;
        return [
            {
                id: candidate.id,
                query: candidate.query,
                fileCount,
                lastSeenCount:
                    typeof candidate.lastSeenCount === "number"
                        ? candidate.lastSeenCount
                        : fileCount,
                hasNewFiles: candidate.hasNewFiles === true,
                name: candidate.name,
                icon: typeof candidate.icon === "string" ? candidate.icon : "",
            },
        ];
    });
};

export interface AutoActionsPreferences {
    markAsSeen: boolean;
    flag: boolean;
    reindex: boolean;
    translate: boolean;
    summarize: boolean;
    describeImage: boolean;
}

/**
 * A page fetched ahead of the user and held back from the result list.
 *
 * Keyed by the cursor it was fetched with, so a page staged for a cursor the
 * list has since moved past is discarded rather than appended out of order.
 */
export interface StagedPage {
    cursorKey: string;
    files: GetFilesFileEntry[];
}

/**
 * Why the last page request failed.
 *
 * `expired` is the point-in-time lapsing, which is recoverable only by opening
 * a new snapshot and starting from the first page; `failed` is anything else
 * and the same request may well work on a retry. The two need different
 * buttons, which is why the kind is kept rather than just a message.
 */
export interface PaginationError {
    kind: "expired" | "failed";
    detail: string;
}

/** Rows of the rendered order on screen, as inclusive indices. */
export interface VisibleRange {
    startIndex: number;
    endIndex: number;
}

export interface PaginationState {
    // Cursor of the page request currently in flight, or null when idle. Scoped
    // to pagination on purpose: the global loading counter is bumped by uploads,
    // tag loads and folder fetches, so gating the result list on it would make
    // the same keypress behave differently depending on an unrelated panel.
    pendingCursorKey: string | null;
    // How many moves past the last loaded card are waiting for that page. Every
    // press counts, so five presses at the boundary advance five cards.
    queuedAdvance: number;
    staged: StagedPage | null;
    // Set when a page request fails. Pages otherwise load on their own as the
    // user scrolls, so this is what stops the list silently going quiet: it
    // both halts the auto-loading and puts a button back for the user to act on.
    error: PaginationError | null;
}

export interface SearchState {
    query: SearchQuery | null;
    queryError?: string;
    leftSidebarPanel: LeftSidebarPanel | null;
    rightSidebarTab: RightSidebarTab | null;
    leftSidebarWidth: number;
    rightSidebarWidth: number;
    stats: CombinedStats;
    bindings: Record<string, string[]>;
    files: {
        [fileId: string]: SearchFileEntry;
    };
    temporaryFileId: string | null;
    totalFiles: number;
    lastFileSortId: any[] | null;
    resultOrder: string[];
    /**
     * Bumped whenever a query replaces the result list wholesale.
     *
     * The reader's position is measured in pixels, and after a replacement
     * those pixels describe a different set of results - so a search run from
     * halfway down the old one would open part-way into the new one, with its
     * best matches above the fold. The view scrolls back to the top when this
     * changes.
     */
    resultsReplaced: number;
    pagination: PaginationState;
    filesInView: string[];
    // Rows of the rendered order currently on screen, or null before the list
    // has reported a range.
    visibleRange: VisibleRange | null;
    tags: string[];
    customQueries: CustomQuery[];
    highlightedQueryId: string | null;
    openFileTabs: OpenFileTab[];
    /** Which tab of the File Detail sidebar is in front. */
    fileDetailSelection: FileDetailSelection;
    /** Sub-tab of the following tab, which has no `OpenFileTab` to hold it. */
    followDetailTab: FileDetailTab;
    expandFilePaths: boolean;
    fieldLayout: FieldLayout;
    previewFields: string[];
    /**
     * Selected fields the reader has picked out, drawn bold on every card.
     *
     * A subset of `previewFields` and kept one by `setPreviewFields`: a field
     * that is no longer on the card has nothing to be bold about, and leaving
     * it here would bring the emphasis back unannounced the next time the
     * field was selected.
     */
    boldPreviewFields: string[];
    /** How many columns a card lays its fields out in, at least one. */
    fieldColumnCount: number;
    /**
     * Which column each selected field is drawn in, zero-based.
     *
     * `previewFields` stays the single order for every column and each one
     * draws its own members in that order, so moving a field between columns
     * cannot disturb the order the line layout reads by position. A field
     * with no entry here is in the first column; entries are dropped with the
     * field they name, and clamped when a column is removed.
     */
    fieldColumnOf: Record<string, number>;
    /**
     * Whether a card names the fields it draws, or shows the values alone.
     *
     * A Card Fields setting and not a card element, so no density preset
     * touches it: the presets decide how much of a card is drawn, and this
     * decides what the fields the reader chose look like.
     */
    showFieldNames: boolean;
    fieldColumnWidths: Record<string, number>;
    thumbnailColumnWidth: number | null;
    availablePreviewFields: PreviewField[];
    fieldExpansion: Record<string, boolean>;
    thumbnailWidthRem: number;
    showHighlights: boolean;
    showExtensionIcon: boolean;
    showFilePath: boolean;
    showParentNavigation: boolean;
    showStatusIndicators: boolean;
    showAttachments: boolean;
    showTags: boolean;
    showActions: boolean;
    showSortIndicator: boolean;
    showFieldActions: boolean;
    autoActionsPreferences: AutoActionsPreferences;
    contentTruncatedFilesCount: number;
    attachmentsSkippedFilesCount: number;
    failedFilesCount: number;
    displayStat: string;
    displayHistogramStat: string;
    termsStats: AvailableStat[];
    histogramStats: AvailableStat[];
    webSocketPubSubMessage: PubSubMessage | null;
    summarizationSystemPrompt: string | null;
    visionSystemPrompt: string | null;
    highlightedFileId: string | null;
    highlightScrollRequest: number;
    highlightScrollMode: "smart" | "top";
    suppressDownloadWarning: boolean;
    folderViewExpandedNodes: string[];
    filteredFolderViewExpandedNodes: string[];
    folderViewOptions: FolderViewOptions;
    filteredFolderViewOptions: FolderViewOptions;
    pendingFullscreenFileId: string | null;
    showChatReasoning: boolean;
}

export const SEARCH_STATE_DOCS = {
    query: "SearchQuery | null — active search query (text, filters, sort)",
    queryError: "string | undefined — validation error for the current query",
    leftSidebarPanel:
        "LeftSidebarPanel | null — active left sidebar panel (folder/tags/queries/card_customization/chat)",
    rightSidebarTab: "RightSidebarTab | null — active right sidebar tab",
    leftSidebarWidth:
        "number — left sidebar width in px, clamped to the viewport on read",
    rightSidebarWidth:
        "number — right sidebar width in px, clamped to the viewport on read",
    stats: "CombinedStats — search statistics (termsData, histogramData)",
    files: "Record<fileId, {meta, preview, query, stale?, temporary?}> — file entry cache: search hits (meta set) plus entries kept for open tabs, fetched previews and the temporary highlight (meta null), so the key count is not the number of results shown",
    temporaryFileId:
        "string | null — ID of a transiently opened file not in search results",
    totalFiles: "number — total result count for the current query",
    lastFileSortId: "any[] | null — sort cursor for pagination",
    resultOrder:
        "string[] — hit IDs of the current query in backend ranking order, one entry per loaded result; the result list renders this, not the key order of `files`",
    resultsReplaced:
        "number — bumped when a query replaces the result list, which sends the view back to the top",
    pagination:
        "PaginationState — {pendingCursorKey, queuedAdvance, staged, error}: the in-flight page request, moves waiting on it, a page fetched ahead of the user, and why the last page request failed ({kind: 'expired'|'failed', detail}) if it did",
    filesInView:
        "string[] — file IDs of the result cards currently on screen. Membership, not order: entries are appended as cards scroll in, so the order follows the scroll direction. The result list in rank order is `resultOrder`",
    visibleRange:
        "{startIndex, endIndex} | null — rows of the rendered order on screen; where the user is, not how much has loaded",
    tags: "string[] — available tags",
    customQueries:
        "CustomQuery[] — saved queries ({id, query, fileCount, lastSeenCount, hasNewFiles, name, icon})",
    highlightedQueryId:
        "string | null — which custom query is highlighted in the sidebar",
    openFileTabs: "OpenFileTab[] — opened file tabs ({fileId, detailTab})",
    fileDetailSelection:
        "FileDetailSelection — which File Detail tab is in front ({kind:'follow'} or {kind:'file',fileId})",
    followDetailTab:
        "FileDetailTab — sub-tab of the following tab, which has no tab entry of its own",
    expandFilePaths:
        "boolean — whether long file paths are shown in full on every result card",
    fieldLayout:
        "FieldLayout — how card metadata fields are rendered (compact|line)",
    previewFields: "string[] — field names shown as preview on cards",
    boldPreviewFields:
        "string[] — subset of previewFields the reader picked out, drawn bold",
    fieldColumnCount: "number — how many columns a card lays its fields out in",
    fieldColumnOf:
        "Record<fieldId, number> — zero-based card column per selected field",
    fieldColumnWidths:
        "Record<fieldName, number> — width in fr of each column in the line field layout, as left by dragging the column borders; a field absent from the map is one that was never dragged",
    thumbnailColumnWidth:
        "number | null — edge length in px of the thumbnail column in the line field layout, as left by dragging its border; null means the density decides",
    availablePreviewFields:
        "PreviewField[] — all fields available for card preview",
    fieldExpansion:
        "Record<fieldName, boolean> — which card field sections are expanded",
    thumbnailWidthRem:
        "number — width of a card's thumbnail column in rem; 0 draws none",
    showHighlights: "boolean — card visibility: search hit highlights",
    showExtensionIcon: "boolean — card visibility: file extension icon",
    showFilePath: "boolean — card visibility: file path",
    showParentNavigation: "boolean — card visibility: parent folder navigation",
    showStatusIndicators:
        "boolean — card visibility: processing status indicators",
    showAttachments: "boolean — card visibility: attachment list",
    showTags: "boolean — card visibility: tag chips",
    showActions: "boolean — card visibility: action buttons",
    showSortIndicator: "boolean — card visibility: sort field indicator",
    showFieldNames:
        "boolean — card visibility: the label ahead of each field's value",
    showFieldActions: "boolean — card visibility: per-field action buttons",
    autoActionsPreferences:
        "AutoActionsPreferences — which auto-actions run on file open (markAsSeen, flag, reindex, translate, summarize, describeImage)",
    contentTruncatedFilesCount:
        "number — files with truncated content in current results",
    attachmentsSkippedFilesCount:
        "number — files with skipped attachments in current results",
    failedFilesCount:
        "number — files that failed processing in current results",
    displayStat: "string — which terms stat is shown in the statistics panel",
    displayHistogramStat:
        "string — which histogram stat is shown in the statistics panel",
    termsStats: "AvailableStat[] — available term aggregation statistics",
    histogramStats: "AvailableStat[] — available histogram statistics",
    webSocketPubSubMessage:
        "PubSubMessage | null — last received WebSocket pub/sub message",
    summarizationSystemPrompt:
        "string | null — custom system prompt for summarization",
    visionSystemPrompt:
        "string | null — custom system prompt for vision/image description",
    highlightedFileId:
        "string | null — file card currently focused/highlighted",
    highlightScrollRequest:
        "number — counter incremented to trigger scroll to highlighted file",
    highlightScrollMode:
        '"smart" | "top" — scroll behaviour when highlighting a file',
    suppressDownloadWarning:
        "boolean — whether the download size warning dialog is suppressed",
    folderViewExpandedNodes: "string[] — expanded node IDs in the folder tree",
    filteredFolderViewExpandedNodes:
        "string[] — expanded node IDs in the filtered folder tree",
    folderViewOptions:
        "FolderViewOptions — folder tree depth limits ({pathDepth, extractionDepth}, null = no limit)",
    filteredFolderViewOptions:
        "FolderViewOptions — depth limits of the filtered folder tree",
    pendingFullscreenFileId:
        "string | null — file ID queued to open in fullscreen",
    showChatReasoning:
        "boolean — whether AI chat reasoning/thinking output is expanded",
    bindings:
        "Record<string, string[]> — custom keyboard shortcut bindings (actionId → keys)",
} satisfies Record<keyof SearchState, string>;

/**
 * How many results one page request asks for.
 *
 * Not a user setting: the list loads on its own as it is scrolled, so this is
 * only the size of a fetch and not something anyone sees. The API's own
 * default is 10, which puts a network boundary every ten cards.
 */
export const RESULT_PAGE_SIZE = 25;

export const QUERY_FAILED_FILES = "state:failed";
export const QUERY_CONTENT_TRUNCATED_FILES = "content_truncated:true";
export const QUERY_ATTACHMENTS_SKIPPED_FILES = "attachments_skipped:true";

export const SEARCH_STATE_LOCAL_STORAGE_KEY = "SEARCH_STATE";

export const loadPersistedSearchState = (): Partial<SearchState> => {
    const data = window.localStorage.getItem(SEARCH_STATE_LOCAL_STORAGE_KEY);
    if (!data) return {};
    try {
        const parsed = JSON.parse(data) as Partial<SearchState>;
        return {
            ...parsed,
            ...("customQueries" in parsed
                ? {
                      customQueries: normalizeCustomQueries(
                          parsed.customQueries,
                      ),
                  }
                : {}),
            ...("folderViewOptions" in parsed
                ? {
                      folderViewOptions: normalizeFolderViewOptions(
                          parsed.folderViewOptions,
                      ),
                  }
                : {}),
            ...("filteredFolderViewOptions" in parsed
                ? {
                      filteredFolderViewOptions: normalizeFolderViewOptions(
                          parsed.filteredFolderViewOptions,
                      ),
                  }
                : {}),
        };
    } catch {
        return {};
    }
};

const persistedState = loadPersistedSearchState();
// Seed the selection from the URL hash so the Redux→URL effect sees a match
// on initial mount and doesn't clear the hash before the URL→Redux effect can
// open the tab. The URL→Redux effect (syncedHashRef = "") still fires and calls
// openFileTabThunk to ensure the tab is added to openFileTabs if it isn't yet.
const initialHashFileId = window.location.hash.substring(1) || null;

const initialState: SearchState = {
    leftSidebarPanel: null,
    rightSidebarTab: null,
    leftSidebarWidth: DEFAULT_LEFT_SIDEBAR_WIDTH,
    rightSidebarWidth: DEFAULT_RIGHT_SIDEBAR_WIDTH,
    stats: { termsData: null, histogramData: null },
    files: {},
    lastFileSortId: null,
    totalFiles: 0,
    resultOrder: [],
    resultsReplaced: 0,
    pagination: {
        pendingCursorKey: null,
        queuedAdvance: 0,
        staged: null,
        error: null,
    },
    filesInView: [],
    visibleRange: null,
    tags: [],
    customQueries: [],
    highlightedQueryId: null,
    openFileTabs: [],
    followDetailTab: FileDetailTab.Rendered,
    expandFilePaths: false,
    fieldLayout: "compact",
    previewFields: ["content"],
    boldPreviewFields: [],
    fieldColumnCount: 1,
    fieldColumnOf: {},
    showFieldNames: true,
    fieldColumnWidths: {},
    thumbnailColumnWidth: null,
    availablePreviewFields: [],
    // The element switches, always authoritative; they start from standard.
    ...CARD_PRESETS.standard,
    fieldExpansion: {},
    autoActionsPreferences: {
        markAsSeen: true,
        flag: false,
        reindex: false,
        translate: false,
        summarize: false,
        describeImage: false,
    },
    contentTruncatedFilesCount: 0,
    attachmentsSkippedFilesCount: 0,
    failedFilesCount: 0,
    displayStat: DEFAULT_TERMS_STAT,
    displayHistogramStat: DEFAULT_HISTOGRAM_STAT,
    termsStats: [],
    histogramStats: [],
    webSocketPubSubMessage: null,
    summarizationSystemPrompt: null,
    visionSystemPrompt: null,
    highlightedFileId: null,
    highlightScrollRequest: 0,
    highlightScrollMode: "smart" as const,
    temporaryFileId: null,
    suppressDownloadWarning: false,
    folderViewExpandedNodes: [],
    filteredFolderViewExpandedNodes: [],
    folderViewOptions: NO_FOLDER_VIEW_LIMITS,
    filteredFolderViewOptions: NO_FOLDER_VIEW_LIMITS,
    pendingFullscreenFileId: null,
    showChatReasoning: false,
    bindings: {},
    ...persistedState,
    // Restore the last query (text + sort) so the search fields come back
    // filled. The results do not survive a reload, so Search re-runs this
    // query on mount whenever the URL does not name one of its own.
    // Strip sortId (pagination cursor) so the first real fetch starts from page 1.
    // The selection always comes from the URL hash.
    query: persistedState.query
        ? { ...(persistedState.query as SearchQuery), sortId: null }
        : null,
    fileDetailSelection: initialHashFileId
        ? fileTab(initialHashFileId)
        : FOLLOW_TAB,
} as SearchState;

/**
 * Identity of a pagination cursor, for comparing one against another.
 *
 * `sortId` is a fresh array on every response, so the cursor cannot be compared
 * by reference and is not usable as an effect dependency. The serialised form is.
 */
export const cursorKey = (cursor: any[] | null): string =>
    JSON.stringify(cursor ?? []);

export interface NextPageResult {
    files: GetFilesFileEntry[];
    cursorKey: string;
    /** The page was already in hand; nothing was fetched for it. */
    fromStaged: boolean;
}

/**
 * Page requests in flight, keyed by cursor.
 *
 * One cursor is one page, so a click that lands while the prefetch for the same
 * cursor is still running attaches to that request instead of issuing a second
 * identical one. This is also what stops a double-click fetching a page twice.
 */
const inFlightPages = new Map<string, Promise<NextPageResult>>();

const loadPageAfter = (
    query: PitBoundSearchQuery,
    cursor: any[],
    pageSize: number,
): Promise<NextPageResult> => {
    const key = cursorKey(cursor);
    const pending = inFlightPages.get(key);
    if (pending) return pending;

    const request = searchFiles({ ...query, sortId: cursor, pageSize })
        .then((response) => ({
            files: response.files,
            cursorKey: key,
            fromStaged: false,
        }))
        .finally(() => inFlightPages.delete(key));

    inFlightPages.set(key, request);
    return request;
};

/**
 * Load the next page into the result list.
 *
 * Takes a staged page when one is in hand, which commits in the same tick as the
 * click — no request, no spinner. Rejected while a request for the same cursor is
 * already in flight, so repeated presses queue moves (`queuedAdvance`) rather than
 * requests.
 */
export const fetchNextPage = createAsyncThunk<
    NextPageResult | null,
    void,
    AsyncThunkConfig
>(
    "fetchNextPageThunk",
    async (_, thunkAPI) => {
        const { search } = thunkAPI.getState() as RootState;
        const cursor = search.lastFileSortId;
        // The cursor only means anything inside the snapshot that produced it, so
        // there is no page to fetch until a point-in-time has been opened.
        const query = search.query?.id
            ? (search.query as PitBoundSearchQuery)
            : null;
        if (!query || cursor === null) return null;

        const staged = search.pagination.staged;
        if (staged && staged.cursorKey === cursorKey(cursor)) {
            return { ...staged, fromStaged: true };
        }
        try {
            return await loadPageAfter(query, cursor, RESULT_PAGE_SIZE);
        } catch (error: any) {
            // Classified rather than reported as one failure, because the two
            // need different recoveries. Note this deliberately does not do
            // what updateQuery does with a 409 and silently reopen from page
            // one: that resets the list under a user who has scrolled into it.
            if (
                error instanceof ResponseError &&
                error.response.status === 409
            ) {
                return thunkAPI.rejectWithValue({
                    kind: "expired",
                    detail: t("generalSearchView.queryExpiredPaging"),
                } satisfies PaginationError);
            }
            let detail = error?.toString() ?? "";
            if (error instanceof ResponseError) {
                const body = await error.response.json().catch(() => null);
                detail = body?.detail ?? detail;
            }
            return thunkAPI.rejectWithValue({
                kind: "failed",
                detail,
            } satisfies PaginationError);
        }
    },
    {
        condition: (_, thunkAPI) => {
            const { search } = thunkAPI.getState() as RootState;
            if (search.pagination.pendingCursorKey === null) return true;
            // Already fetching this exact page.
            return (
                search.pagination.pendingCursorKey !==
                cursorKey(search.lastFileSortId)
            );
        },
    },
);

/**
 * Fetch the next page without showing it.
 *
 * Fired once the Load More button has been sitting in view for a moment, or once
 * the highlight comes within a few cards of the end, so that the page is already
 * in hand by the time it is asked for.
 */
export const prefetchNextPage = createAsyncThunk<
    NextPageResult | null,
    void,
    AsyncThunkConfig
>(
    "prefetchNextPageThunk",
    async (_, thunkAPI) => {
        const { search } = thunkAPI.getState() as RootState;
        const cursor = search.lastFileSortId;
        const query = search.query?.id
            ? (search.query as PitBoundSearchQuery)
            : null;
        if (!query || cursor === null) return null;
        return loadPageAfter(query, cursor, RESULT_PAGE_SIZE);
    },
    {
        condition: (_, thunkAPI) => {
            const { search } = thunkAPI.getState() as RootState;
            const cursor = search.lastFileSortId;
            if (cursor === null) return false;
            if (search.totalFiles <= search.resultOrder.length) return false;
            const key = cursorKey(cursor);
            // Already staged, or already being fetched for real.
            if (search.pagination.staged?.cursorKey === key) return false;
            if (search.pagination.pendingCursorKey === key) return false;
            return !inFlightPages.has(key);
        },
    },
);

export const updateQuery = createAsyncThunk(
    "updateQueryThunk",
    async (query: Partial<SearchQuery>, thunkAPI) => {
        const dispatch = thunkAPI.dispatch;
        const { search } = thunkAPI.getState() as RootState;
        const lastQuery = search.query;
        const lastTotalFiles = search.totalFiles;

        // Keep the keep-alive the point in time was opened with and send it
        // back on every request against that query. Each request extends the
        // snapshot by the keep-alive it carries, so leaving it out would let a
        // long-running query fall back to the much shorter API default and
        // expire while it is still being paged through.
        const openedQuery = query.id ? null : await getLongRunningQuery();
        const queryId = query.id ?? openedQuery?.queryId;
        if (thunkAPI.signal.aborted || !queryId) return;
        const queryQuery = query.query ?? lastQuery?.query ?? "";

        if (!queryQuery.trim()) {
            return;
        }

        const newQuery: PitBoundSearchQuery = {
            id: queryId,
            query: queryQuery,
            keepAlive:
                query.keepAlive ??
                openedQuery?.keepAlive ??
                lastQuery?.keepAlive ??
                null,
            sortField:
                query.sortField !== undefined
                    ? query.sortField?.trim() || null
                    : (lastQuery?.sortField ?? null),
            // Same undefined-check as sortField above, so that a caller
            // describing a whole search - the URL sync does - can say "no
            // direction" with null instead of inheriting the last one.
            sortDirection:
                query.sortDirection !== undefined
                    ? query.sortDirection
                    : (lastQuery?.sortDirection ?? null),
            sortId: query.sortId ?? null,
            pageSize: query.pageSize ?? RESULT_PAGE_SIZE,
        };
        const queryIdChanged = lastQuery?.id !== queryId;
        let querySubscriptionActive = queryIdChanged;
        const cleanupQuerySubscription = () => {
            if (!querySubscriptionActive) return;
            querySubscriptionActive = false;
            dispatch(
                webSocketSendMessage({
                    message: {
                        type: "unsubscribe",
                        channels: new Set([queryId]),
                    },
                }),
            );
        };
        const handleAbort = () => {
            cleanupQuerySubscription();
            dispatch(stopLoadingIndicator());
        };

        dispatch(startLoadingIndicator());

        if (queryIdChanged) {
            dispatch(
                webSocketSendMessage({
                    message: {
                        type: "subscribe",
                        channels: new Set([queryId]),
                    },
                }),
            );
        }
        thunkAPI.signal.addEventListener("abort", handleAbort, { once: true });
        try {
            // The count is only asked for on the first page of a query. It runs
            // with track_total_hits, which is the most expensive thing the API
            // does, and the point in time freezes the answer for the life of the
            // query — so re-counting on every page would pay for a known total.
            const isFirstPage = newQuery.sortId === null;
            const [searchRes, countRes] = await Promise.all([
                searchFiles(newQuery),
                isFirstPage
                    ? getFilesCount(newQuery)
                    : Promise.resolve({ totalFiles: lastTotalFiles }),
            ]);
            if (thunkAPI.signal.aborted) return;

            if (queryIdChanged && lastQuery?.id) {
                dispatch(
                    webSocketSendMessage({
                        message: {
                            type: "unsubscribe",
                            channels: new Set([lastQuery.id]),
                        },
                    }),
                );
            }

            return { ...searchRes, ...countRes, query: newQuery };
        } catch (error: any) {
            if (thunkAPI.signal.aborted) return;
            cleanupQuerySubscription();
            // 409 means the point-in-time this query was paging against has expired.
            // Pages cannot be resumed across snapshots, so the only correct recovery
            // is a fresh snapshot read from the first page: drop the id so a new one
            // is opened, and the sortId that pointed into the old one.
            //
            // Retried only when the caller supplied the id — "load more" does, and
            // that is the request that outlives a snapshot. The retry carries no id,
            // so a 409 on a snapshot opened moments earlier surfaces as the real
            // error it is instead of looping.
            if (
                error instanceof ResponseError &&
                error.response.status === 409 &&
                query.id !== undefined
            ) {
                toast.info(t("generalSearchView.queryExpired"));
                dispatch(
                    updateQuery({ ...query, id: undefined, sortId: null }),
                );
                return;
            }
            // Get error detail
            let errorDetail = error.toString();
            if (error instanceof ResponseError) {
                const errorData = await error.response.json();
                errorDetail = errorData?.detail ?? JSON.stringify(errorData);
            }
            return thunkAPI.rejectWithValue(errorDetail);
        } finally {
            thunkAPI.signal.removeEventListener("abort", handleAbort);
            if (!thunkAPI.signal.aborted) dispatch(stopLoadingIndicator());
        }
    },
);

export const fetchPreview = createAsyncThunk(
    "fetchPreviewThunk",
    async (
        {
            fileId,
            query,
        }: {
            fileId: string;
            query?: SearchQuery;
        },
        thunkAPI: GetThunkAPI<AsyncThunkConfig>,
    ) => {
        const { search } = thunkAPI.getState() as RootState;
        // Stale files are fetched without any query context so they load via
        // "hidden:*" unconditionally — their stored query no longer matches.
        // For non-stale files: use the explicit query if provided, otherwise
        // fall back to the active search query only when the file is in results
        // (to get highlights). Files outside results use "hidden:*".
        const fileEntry = search.files[fileId];
        const fileIsStale = fileEntry?.stale ?? false;
        const fileIsInResults = fileEntry?.meta != null && !fileIsStale;
        const activeQuery = fileIsStale
            ? null
            : (query ?? (fileIsInResults ? search.query : null));

        const searchQuery: SearchQuery = activeQuery
            ? { ...activeQuery, query: activeQuery.query ?? "", id: null }
            : {
                  id: null,
                  query: "hidden:*",
                  keepAlive: null,
                  sortField: null,
                  sortDirection: null,
                  sortId: null,
                  pageSize: null,
              };
        // The indicator fields are drawn from the preview the request already
        // returns, so asking for them would be asking the backend for a field
        // it has never heard of.
        const fields = apiPreviewFields(
            (thunkAPI.getState() as RootState).search.previewFields,
        );
        try {
            return {
                query: searchQuery,
                preview: await getFilePreview(fileId, searchQuery, fields),
                // Carried back so the entry records which field set it holds;
                // isPreviewFresh compares against it.
                fields: fields,
            };
        } catch (err: any) {
            return thunkAPI.rejectWithValue({
                error: err.detail ? err.detail : err.toString(),
                fileId: fileId,
            });
        }
    },
);

export const fetchFilesCountForCustomQuery = createAsyncThunk(
    "fetchFilesCountForCustomQueryThunk",
    async (
        {
            customQueryId,
        }: {
            customQueryId: string;
        },
        thunkAPI,
    ) => {
        // Resolve from state rather than taking the object: the poll loop runs
        // independently of the sidebar, so a query can be deleted between one
        // round being scheduled and this call running.
        const { search } = thunkAPI.getState() as RootState;
        const customQuery = search.customQueries.find(
            (cq) => cq.id === customQueryId,
        );
        if (!customQuery) {
            return thunkAPI.rejectWithValue({
                error: `Unknown custom query: ${customQueryId}`,
            });
        }
        try {
            const response = await getFilesCount({
                ...customQuery.query,
                id: null,
            });
            return { response, customQueryId };
        } catch (err: any) {
            return thunkAPI.rejectWithValue({
                error: err.detail ? err.detail : err.toString(),
            });
        }
    },
);

export const fetchContentTruncatedFiles = createAsyncThunk(
    "fetchContentTruncatedFilesThunk",
    async () => {
        return getFilesCount({
            id: null,
            query: QUERY_CONTENT_TRUNCATED_FILES,
            keepAlive: null,
        });
    },
);

export const fetchAttachmentsSkippedFiles = createAsyncThunk(
    "fetchAttachmentsSkippedFilesThunk",
    async () => {
        return getFilesCount({
            id: null,
            query: QUERY_ATTACHMENTS_SKIPPED_FILES,
            keepAlive: null,
        });
    },
);

export const fetchFailedFiles = createAsyncThunk(
    "fetchFailedFilesThunk",
    async () => {
        return getFilesCount({
            id: null,
            query: QUERY_FAILED_FILES,
            keepAlive: null,
        });
    },
);

/**
 * Make sure a card entering the viewport has a usable preview cached.
 *
 * Dispatched on the false→true edge only. It does not record the in-view
 * state — `fileInViewChanged` does that synchronously — so this is free to be
 * skipped, which is the whole point of the condition below.
 */
export const ensureViewPreview = createAsyncThunk(
    "ensureViewPreviewThunk",
    async (
        {
            fileId,
            query,
        }: {
            fileId: string;
            query?: SearchQuery | null;
        },
        thunkAPI,
    ) => {
        const { search } = thunkAPI.getState() as RootState;
        // The active query is passed explicitly so fetchPreview never falls
        // back to "hidden:*" for a file with a null meta (a temporary card, a
        // stale entry). Reading it here rather than taking it from the caller
        // keeps result cards from depending on the query object's identity.
        await thunkAPI.dispatch(
            fetchPreview({
                fileId: fileId,
                query: query ?? search.query ?? undefined,
            }),
        );
    },
    {
        // Every dispatch of an async thunk costs a pending and a fulfilled
        // action even when it does nothing, and each one re-runs every
        // subscriber. Skip the round trip when the cache already holds a
        // preview this card can render.
        condition: ({ fileId }, { getState }) => {
            const { search } = getState() as RootState;
            return !isPreviewFresh(search.files[fileId], {
                query: search.query,
                // Matched against what was recorded at fetch time, so picking
                // up an indicator field cannot invalidate a cached preview.
                previewFields: apiPreviewFields(search.previewFields),
            });
        },
    },
);

/**
 * Fold one page of hits into the file cache and the result order.
 *
 * Appending to `resultOrder` is what keeps the list in the backend's ranking
 * order: a file the cache already holds — an open tab, a fetched preview, a card
 * that went stale — keeps the slot it was first inserted at in `files`, so
 * deriving the order from that map would put returning hits in the wrong place.
 */
const appendPage = (state: SearchState, files: GetFilesFileEntry[]) => {
    const known = new Set(state.resultOrder);
    files.forEach((file) => {
        if (!state.files[file.fileId]) {
            state.files[file.fileId] = {
                meta: file,
                preview: null,
                query: null,
            };
        } else {
            // Same query, new page: preserve the preview; the file is back in
            // results so clear any stale flag.
            state.files[file.fileId].meta = file;
            state.files[file.fileId].stale = false;
            // A hit is a result, never an out-of-results highlight. Both
            // carriers of that state have to go, or the id is listed twice.
            state.files[file.fileId].temporary = false;
            if (state.temporaryFileId === file.fileId) {
                state.temporaryFileId = null;
            }
        }
        if (!known.has(file.fileId)) {
            known.add(file.fileId);
            state.resultOrder.push(file.fileId);
        }
    });

    if (files.length === 0) {
        // The cursor ran out. Dropping it stops the next request restarting
        // from page one, and the total is corrected to what actually arrived so
        // the Load More button does not sit there offering a page that is not
        // coming.
        state.lastFileSortId = null;
        state.totalFiles = state.resultOrder.length;
        return;
    }
    state.lastFileSortId = files.at(-1)?.sortId ?? state.lastFileSortId;
};

const resetPagination = (state: SearchState) => {
    state.pagination.pendingCursorKey = null;
    state.pagination.queuedAdvance = 0;
    state.pagination.staged = null;
    state.pagination.error = null;
};

export const searchSlice = createSlice({
    name: "search",
    initialState,
    reducers: {
        setLeftSidebarPanel: (
            state,
            action: PayloadAction<LeftSidebarPanel | null>,
        ) => {
            state.leftSidebarPanel = action.payload;
            if (action.payload !== LeftSidebarPanel.QUERIES) {
                state.highlightedQueryId = null;
            }
        },
        setHighlightedQueryId: (
            state,
            action: PayloadAction<string | null>,
        ) => {
            state.highlightedQueryId = action.payload;
        },
        openFileTab: (
            state,
            action: PayloadAction<{
                fileId: string;
                detailTab?: FileDetailTab;
                background?: boolean;
            }>,
        ) => {
            const {
                fileId,
                detailTab = FileDetailTab.Rendered,
                background = false,
            } = action.payload;
            const existing = state.openFileTabs.find(
                (t) => t.fileId === fileId,
            );
            if (!existing) {
                state.openFileTabs.push({ fileId, detailTab });
            }
            if (!background) {
                state.fileDetailSelection = fileTab(fileId);
            }
        },
        closeFileTab: (state, action: PayloadAction<string>) => {
            const fileId = action.payload;
            const idx = state.openFileTabs.findIndex(
                (t) => t.fileId === fileId,
            );
            if (idx === -1) return;
            state.openFileTabs.splice(idx, 1);
            if (state.pendingFullscreenFileId === fileId) {
                state.pendingFullscreenFileId = null;
            }
            // Closing the tab in front falls back to the following tab,
            // never to a neighbour: the reader asked to be rid of this
            // document, not to be handed the one beside it. Closing any
            // other tab leaves them where they were.
            //
            // The following tab is never closable, so the strip is never
            // empty and something is always in front.
            const selection = state.fileDetailSelection;
            if (selection.kind === "file" && selection.fileId === fileId) {
                state.fileDetailSelection = FOLLOW_TAB;
            }
        },
        focusFollowTab: (state) => {
            state.fileDetailSelection = FOLLOW_TAB;
        },
        focusFileTab: (state, action: PayloadAction<string>) => {
            // Guarded so that clicking the tab already in front does not hand
            // out a new selection object, which every consumer of it would
            // re-render for. `FOLLOW_TAB` is one shared value and needs no
            // such guard; a file tab is built per call.
            if (
                state.fileDetailSelection.kind === "file" &&
                state.fileDetailSelection.fileId === action.payload
            ) {
                return;
            }
            state.fileDetailSelection = fileTab(action.payload);
        },
        setDetailTab: (
            state,
            action: PayloadAction<{
                target: FileDetailSelection;
                detailTab: FileDetailTab;
            }>,
        ) => {
            const { target, detailTab } = action.payload;
            if (target.kind === "follow") {
                state.followDetailTab = detailTab;
                return;
            }
            // A file that is not open has no tab, and so no sub-tab to set.
            const tab = state.openFileTabs.find(
                (t) => t.fileId === target.fileId,
            );
            if (tab) tab.detailTab = detailTab;
        },
        setRightSidebarTab: (state, action: PayloadAction<RightSidebarTab>) => {
            state.rightSidebarTab = action.payload;
        },
        toggleRightSidebar: (state) => {
            state.rightSidebarTab =
                state.rightSidebarTab !== null
                    ? null
                    : RightSidebarTab.STATISTICS;
        },
        closeLeftSidebar: (state) => {
            state.leftSidebarPanel = null;
        },
        closeRightSidebar: (state) => {
            state.rightSidebarTab = null;
        },
        addCustomQuery: (state, action: PayloadAction<CustomQuery>) => {
            state.customQueries.push(action.payload);
        },
        deleteCustomQuery: (state, action: PayloadAction<CustomQuery>) => {
            state.customQueries = state.customQueries.filter(
                (cq) => cq.id !== action.payload.id,
            );
        },
        markCustomQueryAsRead: (state, action: PayloadAction<CustomQuery>) => {
            const query = state.customQueries.find(
                (cq) => cq.id === action.payload.id,
            );
            if (!query) return;
            query.hasNewFiles = false;
            // Read fileCount from state, not from the payload: call sites hold
            // a render-time snapshot that a poll may already have superseded.
            query.lastSeenCount = query.fileCount;
        },
        clearStats: (state) => {
            state.stats.termsData = null;
            state.stats.histogramData = null;
        },
        fillTermsData: (
            state,
            action: PayloadAction<TermsStatisticsModel | null>,
        ) => {
            state.stats.termsData = action.payload;
        },
        fillHistogramData: (
            state,
            action: PayloadAction<GroupedHistogramStatisticsModel | null>,
        ) => {
            state.stats.histogramData = action.payload;
        },
        setTags: (state, action: PayloadAction<string[]>) => {
            state.tags = action.payload;
        },
        setWebSocketPubSubMessage: (
            state,
            action: PayloadAction<PubSubMessage>,
        ) => {
            state.webSocketPubSubMessage = action.payload;
        },
        fillTermsStats: (state, action: PayloadAction<AvailableStat[]>) => {
            state.termsStats = action.payload;
        },
        fillHistogramStats: (state, action: PayloadAction<AvailableStat[]>) => {
            state.histogramStats = action.payload;
        },
        setDisplayStat: (state, action: PayloadAction<string>) => {
            state.displayStat = action.payload;
        },
        setDisplayHistogramStat: (state, action: PayloadAction<string>) => {
            state.displayHistogramStat = action.payload;
        },
        setSummarizationSystemPrompt: (
            state,
            action: PayloadAction<string>,
        ) => {
            state.summarizationSystemPrompt = action.payload;
        },
        setVisionSystemPrompt: (state, action: PayloadAction<string>) => {
            state.visionSystemPrompt = action.payload;
        },
        setAutoActionPreference: (
            state,
            action: PayloadAction<{
                key: keyof AutoActionsPreferences;
                value: boolean;
            }>,
        ) => {
            state.autoActionsPreferences[action.payload.key] =
                action.payload.value;
        },
        setSuppressDownloadWarning: (state, action: PayloadAction<boolean>) => {
            state.suppressDownloadWarning = action.payload;
        },
        setLeftSidebarWidth: (state, action: PayloadAction<number>) => {
            state.leftSidebarWidth = clampSidebarWidth(action.payload);
        },
        setRightSidebarWidth: (state, action: PayloadAction<number>) => {
            state.rightSidebarWidth = clampSidebarWidth(action.payload);
        },
        setHighlightedFileId: (state, action: PayloadAction<string | null>) => {
            // Re-highlighting the same card is a no-op for the state but not for
            // the store: the action still notifies every subscriber and re-arms
            // the auto-actions timer. Several callers re-assert the current
            // highlight, so the guard belongs here rather than in each of them.
            if (state.highlightedFileId === action.payload) return;
            state.highlightedFileId = action.payload;
            // Moving the highlight is asking about a different file, so the
            // File Detail sidebar comes back to the tab that follows it. An
            // opened tab is a document the reader parked; it stays open, it
            // just stops being the one in front.
            state.fileDetailSelection = FOLLOW_TAB;
        },
        /**
         * Record moves that land past the last loaded card.
         *
         * The highlight stays where it is and the pending row takes over as the
         * thing on screen that moved; `fetchNextPage.fulfilled` spends the count
         * on the page it brings back.
         */
        queueResultAdvance: (state, action: PayloadAction<number>) => {
            state.pagination.queuedAdvance += Math.max(1, action.payload);
            state.highlightScrollRequest += 1;
            state.highlightScrollMode = "smart";
        },
        clearQueuedAdvance: (state) => {
            state.pagination.queuedAdvance = 0;
        },
        bumpHighlightScroll: {
            reducer: (state, action: PayloadAction<"smart" | "top">) => {
                state.highlightScrollRequest += 1;
                state.highlightScrollMode = action.payload;
            },
            prepare: (mode: "smart" | "top" = "smart") => ({
                payload: mode,
            }),
        },
        /**
         * Record a card entering or leaving the viewport.
         *
         * A plain reducer rather than part of the thunk below, so the write
         * lands in the same tick as the card's effect. Fetching a preview is
         * slow and skippable; this bookkeeping is neither, and a card that is
         * unmounted while still in view has to be able to take itself out of
         * the list on the way down.
         *
         * The removal is unconditional while the add is guarded: an entry
         * evicted from the cache must still be able to leave, or it sits in
         * `filesInView` for the rest of the query.
         */
        fileInViewChanged: (
            state,
            action: PayloadAction<{ fileId: string; inView: boolean }>,
        ) => {
            const { fileId, inView } = action.payload;
            if (!inView) {
                state.filesInView = state.filesInView.filter(
                    (id) => id !== fileId,
                );
                return;
            }
            if (!(fileId in state.files)) return;
            if (!state.filesInView.includes(fileId)) {
                state.filesInView = [...state.filesInView, fileId];
            }
        },
        /**
         * Which rows are currently on screen.
         *
         * Dispatched by the list only when the range actually changes — once
         * per row scrolled past rather than once per frame — so this stays far
         * cheaper than it looks.
         */
        visibleRangeChanged: (
            state,
            action: PayloadAction<VisibleRange | null>,
        ) => {
            state.visibleRange = action.payload;
        },
        setTemporaryFileId: (state, action: PayloadAction<string | null>) => {
            if (
                state.temporaryFileId &&
                state.temporaryFileId !== action.payload
            ) {
                delete state.files[state.temporaryFileId];
            }
            state.temporaryFileId = action.payload;
            if (action.payload && !state.files[action.payload]) {
                state.files[action.payload] = {
                    meta: null,
                    preview: null,
                    query: null,
                    temporary: true,
                };
            }
        },
        setExpandFilePaths: (state, action: PayloadAction<boolean>) => {
            state.expandFilePaths = action.payload;
        },
        // Spacing only. Which elements are shown is the other axis and is
        // left exactly as the user left it.

        // A shortcut to a whole set of switches, not a mode the card stays
        // in: the switches are authoritative afterwards and a reader is free
        // to take any of them somewhere no preset describes.
        applyCardPreset: (state, action: PayloadAction<CardPreset>) => {
            Object.assign(state, CARD_PRESETS[action.payload]);
        },
        // Deliberately does NOT reset the preset: a preset decides which
        // card elements are visible, while fieldLayout
        // only decides how a visible field is drawn. Coupling them would drop
        // the user out of "auto" and freeze visibility behind their back.
        setFieldLayout: (state, action: PayloadAction<FieldLayout>) => {
            state.fieldLayout = action.payload;
        },
        setPreviewFields: (state, action: PayloadAction<string[]>) => {
            state.previewFields = action.payload;
            state.boldPreviewFields = state.boldPreviewFields.filter((id) =>
                action.payload.includes(id),
            );
            state.fieldColumnOf = Object.fromEntries(
                Object.entries(state.fieldColumnOf).filter(([id]) =>
                    action.payload.includes(id),
                ),
            );
        },
        setPreviewFieldColumn: (
            state,
            action: PayloadAction<{ fieldId: string; column: number }>,
        ) => {
            const { fieldId, column } = action.payload;
            if (!state.previewFields.includes(fieldId)) return;
            state.fieldColumnOf[fieldId] = Math.max(
                0,
                Math.min(column, state.fieldColumnCount - 1),
            );
        },
        addFieldColumn: (state) => {
            state.fieldColumnCount = Math.min(
                state.fieldColumnCount + 1,
                MAX_FIELD_COLUMNS,
            );
        },
        // The fields in the column that goes come back to the last one left,
        // rather than being dropped: removing a column is about the layout,
        // and a reader who meant to drop the fields would have removed them.
        removeFieldColumn: (state) => {
            if (state.fieldColumnCount <= 1) return;
            state.fieldColumnCount -= 1;
            const last = state.fieldColumnCount - 1;
            for (const [id, column] of Object.entries(state.fieldColumnOf)) {
                if (column > last) state.fieldColumnOf[id] = last;
            }
        },
        toggleBoldPreviewField: (state, action: PayloadAction<string>) => {
            const fieldId = action.payload;
            state.boldPreviewFields = state.boldPreviewFields.includes(fieldId)
                ? state.boldPreviewFields.filter((id) => id !== fieldId)
                : [...state.boldPreviewFields, fieldId];
        },
        // Replaces the whole map rather than one column: a drag moves the
        // border between two columns, so it always settles two of them.
        setFieldColumnWidths: (
            state,
            action: PayloadAction<Record<string, number>>,
        ) => {
            state.fieldColumnWidths = action.payload;
        },
        // null hands the column back to the density preset.
        setThumbnailColumnWidth: (
            state,
            action: PayloadAction<number | null>,
        ) => {
            state.thumbnailColumnWidth = action.payload;
        },
        setFieldExpansion: (
            state,
            action: PayloadAction<{ field: string; expanded: boolean }>,
        ) => {
            state.fieldExpansion[action.payload.field] =
                action.payload.expanded;
        },
        setAvailablePreviewFields: (
            state,
            action: PayloadAction<PreviewField[]>,
        ) => {
            state.availablePreviewFields = action.payload;
        },
        setThumbnailWidthRem: (state, action: PayloadAction<number>) => {
            state.thumbnailWidthRem = Math.max(
                0,
                Math.min(action.payload, THUMBNAIL_WIDTH_MAX_REM),
            );
        },
        setShowHighlights: (state, action: PayloadAction<boolean>) => {
            state.showHighlights = action.payload;
        },
        setShowFieldNames: (state, action: PayloadAction<boolean>) => {
            state.showFieldNames = action.payload;
        },
        setShowExtensionIcon: (state, action: PayloadAction<boolean>) => {
            state.showExtensionIcon = action.payload;
        },
        setShowFilePath: (state, action: PayloadAction<boolean>) => {
            state.showFilePath = action.payload;
        },
        setShowParentNavigation: (state, action: PayloadAction<boolean>) => {
            state.showParentNavigation = action.payload;
        },
        setShowStatusIndicators: (state, action: PayloadAction<boolean>) => {
            state.showStatusIndicators = action.payload;
        },
        setShowAttachments: (state, action: PayloadAction<boolean>) => {
            state.showAttachments = action.payload;
        },
        setShowTags: (state, action: PayloadAction<boolean>) => {
            state.showTags = action.payload;
        },
        setShowActions: (state, action: PayloadAction<boolean>) => {
            state.showActions = action.payload;
        },
        setShowSortIndicator: (state, action: PayloadAction<boolean>) => {
            state.showSortIndicator = action.payload;
        },
        setShowFieldActions: (state, action: PayloadAction<boolean>) => {
            state.showFieldActions = action.payload;
        },
        setFolderViewExpandedNodes: (
            state,
            action: PayloadAction<string[]>,
        ) => {
            state.folderViewExpandedNodes = action.payload;
        },
        setFilteredFolderViewExpandedNodes: (
            state,
            action: PayloadAction<string[]>,
        ) => {
            state.filteredFolderViewExpandedNodes = action.payload;
        },
        setFolderViewOptions: (
            state,
            action: PayloadAction<FolderViewOptions>,
        ) => {
            state.folderViewOptions = normalizeFolderViewOptions(
                action.payload,
            );
        },
        setFilteredFolderViewOptions: (
            state,
            action: PayloadAction<FolderViewOptions>,
        ) => {
            state.filteredFolderViewOptions = normalizeFolderViewOptions(
                action.payload,
            );
        },
        setPendingFullscreenFileId: (
            state,
            action: PayloadAction<string | null>,
        ) => {
            state.pendingFullscreenFileId = action.payload;
        },
        toggleShowChatReasoning: (state) => {
            state.showChatReasoning = !state.showChatReasoning;
        },
        setFilePreview: (
            state,
            action: PayloadAction<GetFilePreviewResponse>,
        ) => {
            const preview = action.payload;
            if (state.files[preview.fileId]) {
                state.files[preview.fileId].preview = preview;
            }
        },
        /**
         * Apply one file update to the cached preview and leave the rest of it
         * alone.
         *
         * Writing a whole preview assembled from a copy read earlier lets two
         * overlapping updates fight: the automatic mark-as-seen and a keypress
         * a few milliseconds later each rebuild the preview from the state they
         * read, so whichever request finishes last wins and the card can be
         * left showing the opposite of what the server holds.
         */
        patchFilePreview: (
            state,
            action: PayloadAction<{
                fileId: string;
                changes: Partial<GetFilePreviewResponse>;
            }>,
        ) => {
            const entry = state.files[action.payload.fileId];
            if (entry?.preview) {
                Object.assign(entry.preview, action.payload.changes);
            }
        },
        setBinding: (
            state,
            action: PayloadAction<{ actionId: string; keys: string[] }>,
        ) => {
            state.bindings[action.payload.actionId] = [
                action.payload.keys.join(" + "),
            ];
        },
        resetBinding: (state, action: PayloadAction<string>) => {
            delete state.bindings[action.payload];
        },
        resetAllBindings: (state) => {
            state.bindings = {};
        },
    },
    extraReducers: (builder) => {
        builder
            .addCase(
                fetchFilesCountForCustomQuery.fulfilled,
                (state, action) => {
                    const customQuery = state.customQueries.find(
                        (cq) => cq.id === action.payload.customQueryId,
                    );
                    if (!customQuery) return;

                    const newFileCount = action.payload.response.totalFiles;
                    // Compare against lastSeenCount, not fileCount: fileCount
                    // tracks every poll, so comparing against it would let a
                    // drop in matches quietly raise the bar for the next badge.
                    customQuery.hasNewFiles =
                        newFileCount > customQuery.lastSeenCount ||
                        customQuery.hasNewFiles; // has new files or already had new files
                    customQuery.fileCount = newFileCount;
                },
            )
            .addCase(fetchContentTruncatedFiles.fulfilled, (state, action) => {
                state.contentTruncatedFilesCount = action.payload.totalFiles;
            })
            .addCase(
                fetchAttachmentsSkippedFiles.fulfilled,
                (state, action) => {
                    state.attachmentsSkippedFilesCount =
                        action.payload.totalFiles;
                },
            )
            .addCase(fetchFailedFiles.fulfilled, (state, action) => {
                state.failedFilesCount = action.payload.totalFiles;
            })
            .addCase(updateQuery.fulfilled, (state, action) => {
                if (!action.payload) {
                    if (state.query) state.query.query = "";
                    state.totalFiles = 0;
                    state.resultOrder = [];
                    resetPagination(state);
                    Object.keys(state.files).forEach((fileId) => {
                        state.files[fileId].meta = null;
                    });
                    if (state.temporaryFileId) {
                        delete state.files[state.temporaryFileId];
                        state.temporaryFileId = null;
                    }
                    return;
                }
                const isNewQuery = state.query?.id !== action.payload.query.id;
                // Computed before files change so we can use them after.
                const isInitialLoad = state.query === null;
                const isSameQueryString =
                    state.query?.query === action.payload.query.query;
                if (isNewQuery) {
                    // Preserve files that have open tabs so their panels stay intact,
                    // but null out meta so they don't appear in the search results card view.
                    // Stale cards are intentionally cleared here so they don't accumulate.
                    const openTabIds = new Set(
                        state.openFileTabs.map((t) => t.fileId),
                    );
                    const preserved: typeof state.files = {};
                    openTabIds.forEach((id) => {
                        if (state.files[id]) {
                            preserved[id] = {
                                ...state.files[id],
                                meta: null,
                                // The highlight does not survive a new query,
                                // so a flag carried over here would never be
                                // cleared: the entry would keep claiming to
                                // exist only for a highlight that is gone. The
                                // keep-alive branch below restores the flag
                                // where it still applies.
                                temporary: false,
                            };
                        }
                    });
                    // For ID-only changes (keep-alive renewal, React strict-mode
                    // double-mount with the same query string), also preserve the
                    // temporary file so an out-of-results highlight is not lost.
                    if (
                        isSameQueryString &&
                        state.temporaryFileId &&
                        state.files[state.temporaryFileId]
                    ) {
                        preserved[state.temporaryFileId] =
                            state.files[state.temporaryFileId];
                    }
                    if (isSameQueryString) {
                        // The same search, asked again - coming back from
                        // another page re-runs it, and so does a keep-alive
                        // renewal. Only the snapshot id is new, and a preview
                        // does not describe the snapshot: `isPreviewFresh`
                        // judges one by the query string and the field set and
                        // ignores the id entirely. Dropping them here would
                        // leave every card already on screen showing a
                        // skeleton that nothing refills - the cards keep
                        // their identity across the re-run, so no card asks
                        // again, and the list stays that way until a
                        // different search replaces it.
                        Object.entries(state.files).forEach(([id, entry]) => {
                            if (preserved[id] || entry.preview == null) return;
                            preserved[id] = { ...entry, meta: null };
                        });
                    }
                    state.files = preserved;
                    if (!isSameQueryString) {
                        state.filesInView = [];
                        // The list is rebuilt from the top, so whatever was on
                        // screen is gone along with it. Asking the same
                        // question again leaves the same cards on screen, and
                        // clearing these would leave nothing to repopulate
                        // them: both are only ever written on a *change*, so
                        // the view count would read empty and a preview-field
                        // change would stop refetching what is in view.
                        state.visibleRange = null;
                    }
                    // For pure ID changes (keep-alive renewal, React strict-mode
                    // double-mount) preserve the current index and temporary file unchanged.
                    // For a genuine new search query capture the highlighted file ID
                    // so it can be restored once the new results arrive below.
                    if (!isSameQueryString && !isInitialLoad) {
                        state.highlightedFileId = null;
                    }
                    if (!isSameQueryString) {
                        state.temporaryFileId = null;
                    }
                }

                state.query = action.payload.query;
                // `updateQuery` only ever delivers the first page of a query —
                // later pages go through `fetchNextPage` — so the order starts
                // fresh here rather than growing.
                state.resultOrder = [];
                state.resultsReplaced += 1;
                state.lastFileSortId = null;
                resetPagination(state);
                appendPage(state, action.payload.files);
                state.totalFiles = action.payload.totalFiles;
                state.queryError = undefined;
                // A rebuild after the point in time was recycled drops every
                // card except open tabs. Leaving the highlight on one of them
                // would leave it naming a card that is not rendered, which the
                // next move silently resolves to the top of the list.
                if (
                    state.highlightedFileId &&
                    !state.files[state.highlightedFileId]
                ) {
                    state.highlightedFileId = null;
                }
            })
            .addCase(updateQuery.pending, (state) => {
                // Bumped here as well as on fulfilment. The list is about to
                // be replaced, and the view has to leave the old position
                // while the old content is still tall enough to hold it -
                // once the shorter result set has rendered the browser has
                // already clamped the scroll to its bottom, and a reset after
                // that reads as "the reader scrolled there".
                state.resultsReplaced += 1;
            })
            .addCase(updateQuery.rejected, (state, action: any) => {
                if (action.meta.aborted) return;
                state.queryError = action.payload;
                toast.error(
                    t("error.searchResultLoadingError", {
                        error: action.payload,
                    }),
                );
            })
            .addCase(fetchNextPage.pending, (state) => {
                state.pagination.pendingCursorKey = cursorKey(
                    state.lastFileSortId,
                );
                state.pagination.error = null;
            })
            .addCase(fetchNextPage.fulfilled, (state, action) => {
                state.pagination.pendingCursorKey = null;
                state.pagination.error = null;
                if (!action.payload) {
                    state.pagination.queuedAdvance = 0;
                    return;
                }
                // Drop a page the list has moved past — a request still in
                // flight when a new query lands would otherwise append the old
                // query's hits to the new query's results.
                if (
                    action.payload.cursorKey !== cursorKey(state.lastFileSortId)
                ) {
                    state.pagination.queuedAdvance = 0;
                    return;
                }
                if (
                    state.pagination.staged?.cursorKey ===
                    action.payload.cursorKey
                ) {
                    state.pagination.staged = null;
                }
                const firstNewIndex = state.resultOrder.length;
                appendPage(state, action.payload.files);

                // Spend the queued moves on the page they were waiting for. One
                // press at the boundary lands on the first new card, three land
                // on the third — clamped to what actually arrived.
                const queued = state.pagination.queuedAdvance;
                state.pagination.queuedAdvance = 0;
                if (queued <= 0) return;
                const target = Math.min(
                    firstNewIndex + queued - 1,
                    state.resultOrder.length - 1,
                );
                if (target < 0) return;
                state.highlightedFileId = state.resultOrder[target];
                state.highlightScrollRequest += 1;
                state.highlightScrollMode = "smart";
            })
            .addCase(fetchNextPage.rejected, (state, action) => {
                // A rejection from the `condition` guard means a request for
                // this page is already running; it will spend the queue.
                if (action.meta.condition) return;
                state.pagination.pendingCursorKey = null;
                state.pagination.queuedAdvance = 0;
                // Pages load on their own as the user scrolls, so without this
                // a failure would read as "that is all there is". It also
                // stops the sentinel re-firing the same failing request.
                state.pagination.error =
                    (action.payload as PaginationError | undefined) ?? null;
            })
            .addCase(prefetchNextPage.fulfilled, (state, action) => {
                if (!action.payload) return;
                // Only stage a page the list is still waiting for: by the time
                // this lands the user may have paged past it by other means.
                if (
                    action.payload.cursorKey !== cursorKey(state.lastFileSortId)
                )
                    return;
                state.pagination.staged = {
                    cursorKey: action.payload.cursorKey,
                    files: action.payload.files,
                };
            })
            .addCase(fetchPreview.fulfilled, (state, action) => {
                if (!action.payload) return;
                const { query, preview, fields } = action.payload;
                const file = state.files[preview.fileId];
                if (file) {
                    file.preview = preview;
                    file.query = query;
                    file.previewFields = fields;
                    file.previewFetchedAt = Date.now();
                } else {
                    state.files[preview.fileId] = {
                        meta: null,
                        preview: preview,
                        query: query,
                        previewFields: fields,
                        previewFetchedAt: Date.now(),
                    };
                }
            })
            .addCase(fetchPreview.rejected, (state, action) => {
                const { fileId } = action.payload as {
                    fileId: string;
                };

                // Mark as stale instead of deleting so the card stays visible
                // when a file no longer matches the current query. Clear the
                // query so fetchFileContent doesn't fire with the stale query
                // before fetchPreview returns a fresh hidden:* one.
                if (fileId && state.files[fileId]) {
                    state.files[fileId].stale = true;
                    state.files[fileId].query = null;
                }
            });
    },
});

export const {
    setLeftSidebarPanel,
    closeLeftSidebar,
    closeRightSidebar,
    setHighlightedQueryId,
    openFileTab,
    closeFileTab,
    focusFollowTab,
    focusFileTab,
    setDetailTab,
    setRightSidebarTab,
    toggleRightSidebar,
    addCustomQuery,
    deleteCustomQuery,
    markCustomQueryAsRead,
    clearStats,
    fillTermsData,
    fillHistogramData,
    fillTermsStats,
    fillHistogramStats,
    setTags,
    setWebSocketPubSubMessage,
    setDisplayStat,
    setDisplayHistogramStat,
    setSummarizationSystemPrompt,
    setVisionSystemPrompt,
    setFilePreview,
    patchFilePreview,
    setHighlightedFileId,
    setLeftSidebarWidth,
    setRightSidebarWidth,
    bumpHighlightScroll,
    queueResultAdvance,
    clearQueuedAdvance,
    setTemporaryFileId,
    fileInViewChanged,
    visibleRangeChanged,
    setAutoActionPreference,
    setExpandFilePaths,
    setSuppressDownloadWarning,
    setFolderViewExpandedNodes,
    setFilteredFolderViewExpandedNodes,
    setFolderViewOptions,
    setFilteredFolderViewOptions,
    setPendingFullscreenFileId,
    applyCardPreset,
    setFieldLayout,

    setPreviewFields,
    toggleBoldPreviewField,
    setPreviewFieldColumn,
    addFieldColumn,
    removeFieldColumn,
    setFieldColumnWidths,
    setThumbnailColumnWidth,
    setAvailablePreviewFields,
    setFieldExpansion,
    setThumbnailWidthRem,
    setShowHighlights,
    setShowFieldNames,
    setShowExtensionIcon,
    setShowFilePath,
    setShowParentNavigation,
    setShowStatusIndicators,
    setShowAttachments,
    setShowTags,
    setShowActions,
    setShowSortIndicator,
    setShowFieldActions,
    toggleShowChatReasoning,
    setBinding,
    resetBinding,
    resetAllBindings,
} = searchSlice.actions;

export const openFileTabThunk = createAsyncThunk(
    "openFileTabThunk",
    (
        payload: {
            fileId: string;
            detailTab?: FileDetailTab;
            background?: boolean;
        },
        thunkAPI,
    ) => {
        thunkAPI.dispatch(openFileTab(payload));
        // A tab nobody can see is not an opened tab. The strip lives in the
        // right sidebar, so opening one reveals it - background opens too,
        // where the strip appearing is the only feedback the reader gets.
        // Dispatched here rather than at each of the dozen call sites: a card
        // double-click, an attachment chip, a chat citation and a pasted
        // #fileId all mean "show me this".
        thunkAPI.dispatch(setRightSidebarTab(RightSidebarTab.FILE_DETAIL));
        // The channel is not subscribed here: `useOpenFileTabSubscriptions`
        // holds exactly one per open tab, which is the only way a re-open of
        // an already-open tab cannot raise a count nothing releases.
    },
);

export const closeFileTabThunk = createAsyncThunk(
    "closeFileTabThunk",
    (fileId: string, thunkAPI) => {
        thunkAPI.dispatch(closeFileTab(fileId));
    },
);

/** Highlight `fileId`, fetching it first when it sits outside the results. */
export const revealFileThunk = createAsyncThunk(
    "revealFileThunk",
    ({ fileId }: { fileId: string }, thunkAPI) => {
        const state = thunkAPI.getState() as RootState;
        const files = state.search.files;

        if (!files[fileId]?.meta && fileId !== state.search.highlightedFileId) {
            thunkAPI.dispatch(setTemporaryFileId(fileId));
            thunkAPI.dispatch(fetchPreview({ fileId }));
        }
        thunkAPI.dispatch(setHighlightedFileId(fileId));
        thunkAPI.dispatch(bumpHighlightScroll("top"));
    },
);

export const selectSearch = (state: RootState) => state.search;

export const selectCustomQueries = createSelector(
    selectSearch,
    (search) => search.customQueries,
);

export const selectLeftSidebarPanel = createSelector(
    selectSearch,
    (search) => search.leftSidebarPanel,
);

export const selectHighlightedQueryId = createSelector(
    selectSearch,
    (search) => search.highlightedQueryId,
);

export const selectOpenFileTabs = createSelector(
    selectSearch,
    (search) => search.openFileTabs,
);

export const selectFileDetailSelection = createSelector(
    selectSearch,
    (search) => search.fileDetailSelection,
);

export const selectFollowDetailTab = createSelector(
    selectSearch,
    (search) => search.followDetailTab,
);

export const selectRightSidebarOpen = createSelector(
    selectSearch,
    (search) => search.rightSidebarTab !== null,
);

export const selectLeftSidebarWidth = createSelector(
    selectSearch,
    (search) => search.leftSidebarWidth,
);

export const selectRightSidebarWidth = createSelector(
    selectSearch,
    (search) => search.rightSidebarWidth,
);

export const selectRightSidebarTab = createSelector(
    selectSearch,
    (search) => search.rightSidebarTab,
);

export const selectAutoActionsPreferences = createSelector(
    selectSearch,
    (search) => search.autoActionsPreferences,
);

export const selectSuppressDownloadWarning = createSelector(
    selectSearch,
    (search) => search.suppressDownloadWarning,
);

export const selectQuery = createSelector(
    selectSearch,
    (search) => search.query,
);

export const selectQueryError = createSelector(
    selectSearch,
    (search) => search.queryError,
);

export const selectTags = createSelector(selectSearch, (search) => search.tags);

export const selectFiles = createSelector(
    selectSearch,
    (search) => search.files,
);
export const selectLastFileSortId = createSelector(
    selectSearch,
    (search) => search.lastFileSortId,
);

// A plain lookup rather than a memoised-selector factory: a caller building a
// fresh createSelector on every render has a cache that is never warm, and
// every card re-creates its subscription on each pass.
export const selectFileById = (
    state: RootState,
    fileId: string,
): SearchFileEntry | undefined => state.search.files[fileId];

export const selectStatsData = createSelector(
    selectSearch,
    (search) => search.stats,
);

export const selectContentTruncatedFilesCount = createSelector(
    selectSearch,
    (search) => search.contentTruncatedFilesCount,
);

export const selectAttachmentsSkippedFilesCount = createSelector(
    selectSearch,
    (search) => search.attachmentsSkippedFilesCount,
);

export const selectFailedFilesCount = createSelector(
    selectSearch,
    (search) => search.failedFilesCount,
);

export const selectTotalFiles = createSelector(
    selectSearch,
    (search) => search.totalFiles,
);
export const selectResultOrder = createSelector(
    selectSearch,
    (search) => search.resultOrder,
);

// How many hits of the current query have been loaded. `resultOrder` holds one
// entry per hit the backend has reported for this query, in its ranking order,
// so this is a length rather than a scan of the file cache — which also holds
// open tabs, fetched previews and the temporary highlight. A stale card keeps
// its slot, because it stays on screen as a result.
export const selectLoadedFiles = createSelector(
    selectResultOrder,
    (resultOrder) => resultOrder.length,
);

export const selectFilesInView = createSelector(
    selectSearch,
    (search) => search.filesInView,
);

// The on-screen cards in the order they are rendered. `filesInView` itself is
// appended to as cards scroll in, so scrolling up builds it backwards; anything
// reporting the visible files to a user or a model wants this instead. An id
// with no rank — the temporary card — sorts to the front, where it renders.
export const selectFilesInViewOrdered = createSelector(
    [selectFilesInView, selectResultOrder],
    (filesInView, resultOrder) => {
        const rank = new Map(resultOrder.map((id, index) => [id, index]));
        return [...filesInView].sort(
            (a, b) => (rank.get(a) ?? -1) - (rank.get(b) ?? -1),
        );
    },
);

export const selectDisplayStat = createSelector(
    selectSearch,
    (search) => search.displayStat,
);

export const selectDisplayHistogramStat = createSelector(
    selectSearch,
    (search) => search.displayHistogramStat,
);

export const selectHistogramData = createSelector(
    selectSearch,
    (search) => search.stats.histogramData,
);

export const selectTermsStats = createSelector(
    selectSearch,
    (search) => search.termsStats,
);

export const selectHistogramStats = createSelector(
    selectSearch,
    (search) => search.histogramStats,
);

export const selectWebSocketPubSubMessage = createSelector(
    selectSearch,
    (search) => search.webSocketPubSubMessage,
);

export const selectSummarizationSystemPrompt = createSelector(
    selectSearch,
    (search) => search.summarizationSystemPrompt,
);

export const selectVisionSystemPrompt = createSelector(
    selectSearch,
    (search) => search.visionSystemPrompt,
);

export const selectTemporaryFileId = createSelector(
    selectSearch,
    (search) => search.temporaryFileId,
);

export const selectExpandFilePaths = createSelector(
    selectSearch,
    (search) => search.expandFilePaths,
);

// Ordered file IDs matching the order DetailedView renders: the temporary
// out-of-results highlight first, then the results in backend ranking order.
// This is the index space the virtualized list is built on, so it has to agree
// with the rendered order element for element.
//
// Built from `temporaryFileId` rather than by scanning `files` for the per-entry
// `temporary` flag: the flag is still maintained by setTemporaryFileId, but the
// pointer is the single source of truth for what is rendered, and depending on
// the whole `files` map returns a fresh array on every preview that arrives.
// With no temporary card this returns `resultOrder` itself, so the identity is
// stable until a page lands.
export const selectResultsReplaced = createSelector(
    selectSearch,
    (search) => search.resultsReplaced,
);

export const selectOrderedFileIds = createSelector(
    [selectResultOrder, selectTemporaryFileId],
    (resultOrder, temporaryFileId) => {
        if (temporaryFileId === null || resultOrder.includes(temporaryFileId)) {
            return resultOrder;
        }
        return [temporaryFileId, ...resultOrder];
    },
);

/**
 * Why the last page request failed, or null.
 *
 * Non-null stops the list auto-loading and puts a button back: `expired` needs
 * a new snapshot from the first page, `failed` can simply be retried.
 */
export const selectPaginationError = createSelector(
    selectSearch,
    (search) => search.pagination.error,
);

/** A page request is in flight — not "anything in the app is loading". */
export const selectIsPaginating = createSelector(
    selectSearch,
    (search) => search.pagination.pendingCursorKey !== null,
);

export const selectQueuedAdvance = createSelector(
    selectSearch,
    (search) => search.pagination.queuedAdvance,
);

// Serialised cursor, so effects can depend on "which page is next" without
// depending on the array identity `sortId` gets on every response.
export const selectPaginationCursorKey = createSelector(
    selectLastFileSortId,
    (sortId) => cursorKey(sortId),
);

export const selectHasMoreResults = createSelector(
    selectSearch,
    (search) =>
        search.lastFileSortId !== null &&
        search.totalFiles > search.resultOrder.length,
);

export const selectHighlightedFileId = createSelector(
    selectSearch,
    (search) => search.highlightedFileId,
);

/**
 * The file the File Detail sidebar is actually showing.
 *
 * Null when the sidebar is closed, on another tab, or on the following tab
 * with nothing highlighted. The selection alone cannot answer this: a tab
 * stays selected while the pane it lives in is shut.
 */
export const selectFileDetailFileId = createSelector(
    [selectRightSidebarTab, selectFileDetailSelection, selectHighlightedFileId],
    (rightTab, selection, highlightedFileId) =>
        rightTab === RightSidebarTab.FILE_DETAIL
            ? selectedFileIdOf(selection, highlightedFileId)
            : null,
);

export const selectVisibleRange = createSelector(
    selectSearch,
    (search) => search.visibleRange,
);

/**
 * 1-based rank of the result the user is currently on, or null before the
 * list has reported where it is.
 *
 * Reported instead of "how many cards are loaded", which with auto-loading is
 * a property of how far the list has fetched rather than of anything the user
 * did, and which ticks upward on its own while they read.
 *
 * The highlighted card wins while it is on screen, so walking the list with
 * the arrow keys moves this one result at a time and lands on the last one.
 * Once it is scrolled out of sight it stops being where the user is, and the
 * lowest visible result takes over — which is also what makes scrolling to the
 * bottom of the list report the end of it. Reading the topmost visible result
 * instead could never reach the total at all: the last screenful does not
 * scroll, so the top of it stays a screen short forever.
 */
export const selectCurrentResultRank = createSelector(
    [
        selectVisibleRange,
        selectHighlightedFileId,
        selectResultOrder,
        selectOrderedFileIds,
    ],
    (
        visibleRange,
        highlightedFileId,
        resultOrder,
        orderedFileIds,
    ): number | null => {
        if (visibleRange === null || resultOrder.length === 0) return null;
        // Rows lead with the temporary out-of-results card when there is one,
        // and it has no rank in the result set.
        const temporaryRows = orderedFileIds.length - resultOrder.length;
        const rankOf = (index: number) => index + 1 - temporaryRows;

        const highlighted = highlightedFileId
            ? orderedFileIds.indexOf(highlightedFileId)
            : -1;
        const onScreen =
            highlighted >= visibleRange.startIndex &&
            highlighted <= visibleRange.endIndex;
        // Falls through to the viewport when the highlight is the temporary
        // card, which has no rank to report.
        if (onScreen && rankOf(highlighted) >= 1) return rankOf(highlighted);

        const fromViewport = rankOf(visibleRange.endIndex);
        if (fromViewport < 1) return null;
        return Math.min(fromViewport, resultOrder.length);
    },
);

export const selectHighlightScrollRequest = createSelector(
    selectSearch,
    (search) => search.highlightScrollRequest,
);

export const selectHighlightScrollMode = createSelector(
    selectSearch,
    (search) => search.highlightScrollMode,
);

export const selectPendingFullscreenFileId = createSelector(
    selectSearch,
    (search) => search.pendingFullscreenFileId,
);

export const selectFolderViewExpandedNodes = createSelector(
    selectSearch,
    (search) => search.folderViewExpandedNodes,
);

export const selectFilteredFolderViewExpandedNodes = createSelector(
    selectSearch,
    (search) => search.filteredFolderViewExpandedNodes,
);

export const selectFolderViewOptions = createSelector(
    selectSearch,
    (search) => search.folderViewOptions,
);

export const selectFilteredFolderViewOptions = createSelector(
    selectSearch,
    (search) => search.filteredFolderViewOptions,
);

export const selectFieldLayout = createSelector(
    selectSearch,
    (search) => search.fieldLayout,
);

export const selectFieldExpansion = createSelector(
    selectSearch,
    (search) => search.fieldExpansion,
);

export const selectPreviewFields = createSelector(
    selectSearch,
    (search) => search.previewFields,
);

export const selectFieldColumnCount = createSelector(
    selectSearch,
    (search) => search.fieldColumnCount,
);

export const selectFieldColumnOf = createSelector(
    selectSearch,
    (search) => search.fieldColumnOf,
);

export const selectShowFieldNames = createSelector(
    selectSearch,
    (search) => search.showFieldNames,
);

export const selectBoldPreviewFields = createSelector(
    selectSearch,
    (search) => search.boldPreviewFields,
);

export const selectFieldColumnWidths = createSelector(
    selectSearch,
    (search) => search.fieldColumnWidths,
);

export const selectThumbnailColumnWidth = createSelector(
    selectSearch,
    (search) => search.thumbnailColumnWidth,
);

export const selectAvailablePreviewFields = createSelector(
    selectSearch,
    (search) => search.availablePreviewFields,
);

export const selectThumbnailWidthRem = createSelector(
    selectSearch,
    (search) => search.thumbnailWidthRem,
);

export const selectShowHighlights = createSelector(
    selectSearch,
    (search) => search.showHighlights,
);

/**
 * The twelve switches as one object.
 *
 * Each flag is its own input rather than the slice as a whole: every mounted
 * card subscribes to this, and taking `search` would rebuild the object on
 * every action — a highlight move, a preview arriving — and re-render all of
 * them for nothing.
 */
export const selectCardElementVisibility = createSelector(
    [
        (state: RootState) => state.search.thumbnailWidthRem,
        (state: RootState) => state.search.showHighlights,
        (state: RootState) => state.search.showExtensionIcon,
        (state: RootState) => state.search.showFilePath,
        (state: RootState) => state.search.showParentNavigation,
        (state: RootState) => state.search.showStatusIndicators,
        (state: RootState) => state.search.showAttachments,
        (state: RootState) => state.search.showTags,
        (state: RootState) => state.search.showActions,
        (state: RootState) => state.search.showSortIndicator,
        (state: RootState) => state.search.showFieldActions,
    ],
    (
        thumbnailWidthRem,
        showHighlights,
        showExtensionIcon,
        showFilePath,
        showParentNavigation,
        showStatusIndicators,
        showAttachments,
        showTags,
        showActions,
        showSortIndicator,
        showFieldActions,
    ): CardVisibilitySettings => ({
        thumbnailWidthRem,
        showHighlights,
        showExtensionIcon,
        showFilePath,
        showParentNavigation,
        showStatusIndicators,
        showAttachments,
        showTags,
        showActions,
        showSortIndicator,
        showFieldActions,
    }),
);

/**
 * The preset the card currently reads as, or null once the switches have been
 * taken somewhere no preset describes.
 *
 * Derived rather than stored: a "custom" flag is this same observation kept
 * as state, and state that restates what is already knowable is state that
 * can disagree with it.
 */
export const selectMatchingCardPreset = createSelector(
    selectCardElementVisibility,
    (visibility): CardPreset | null =>
        (Object.keys(CARD_PRESETS) as CardPreset[]).find((preset) =>
            matchesPreset(visibility, CARD_PRESETS[preset]),
        ) ?? null,
);

export const selectShowChatReasoning = createSelector(
    selectSearch,
    (search) => search.showChatReasoning,
);

export const selectShortcutsBindings = createSelector(
    selectSearch,
    (search) => search.bindings,
);

export const selectResolvedBindings = createSelector(
    [selectShortcutsBindings],
    (bindings) => {
        const resolved: Record<string, string[]> = {};
        for (const action of shortcutRegistry) {
            resolved[action.id] =
                bindings[action.id] !== undefined
                    ? bindings[action.id]
                    : action.defaultKeys;
        }
        return resolved;
    },
);

export const selectReverseBindings = createSelector(
    selectResolvedBindings,
    (resolvedBindings) => {
        const reverse: Record<string, string> = {};
        for (const [actionId, keys] of Object.entries(resolvedBindings)) {
            for (const key of keys) {
                // Normalize the key for case-insensitive matching
                const normalizedKey = key
                    .split(" + ")
                    .map((part) => part.trim().toLowerCase())
                    .join(" + ");
                reverse[normalizedKey] = actionId;
            }
        }
        return reverse;
    },
);

export default searchSlice.reducer;
