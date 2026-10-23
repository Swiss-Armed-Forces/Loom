import { PitBoundSearchQuery, SearchQuery } from "@features/common/utils/model";

import { apiConfiguration } from "./apiConfiguration";
import {
    AiApi,
    ArchivesApi,
    FilesApi,
    ImageDescriptionApi,
    IndexApi,
    SummarizationApi,
    TagsApi,
    TranslationApi,
    AvailableStat,
    GetFilesResponse,
    GetFilesTreeResponse,
    GroupedHistogramStatisticsModel,
    TermsStatisticsModel,
    GetFileResponse,
    GetFilePreviewResponse,
    ArchiveCreatedResponse,
    ContextCreateResponse,
    ContextHistoryResponse,
    ListContextsResponse,
    GetQueryResponse,
    GetFilesCountResponse,
    UpdateFileRequest,
    PreviewField,
    ModeUpdate,
    SearchAfterCursor,
    SearchByFilenameResponse,
} from "./generated";

const filesApi = new FilesApi(apiConfiguration);
const translationApi = new TranslationApi(apiConfiguration);
const archivesApi = new ArchivesApi(apiConfiguration);
const indexApi = new IndexApi(apiConfiguration);
const summarizationApi = new SummarizationApi(apiConfiguration);
const tagsApi = new TagsApi(apiConfiguration);
const aiApi = new AiApi(apiConfiguration);
const imageDescriptionApi = new ImageDescriptionApi(apiConfiguration);

export const loadTags = async (): Promise<string[]> => {
    return tagsApi.getTagsV1FilesTagsGet();
};

export const loadSummarizationSystemPrompt = async (): Promise<string> => {
    return summarizationApi.getSystemPromptV1FilesSummarizationSystemPromptGet();
};

export const loadVisionSystemPrompt = async (): Promise<string> => {
    return imageDescriptionApi.getSystemPromptV1FilesImageDescriptionSystemPromptGet();
};

export const getLongRunningQuery = async (): Promise<GetQueryResponse> => {
    return filesApi.getQueryV1FilesQueryPost({ keepAlive: "30m" });
};

export const searchFiles = async (
    query: PitBoundSearchQuery,
): Promise<GetFilesResponse> => {
    return filesApi.getFilesV1FilesGet({
        queryId: query.id,
        keepAlive: query.keepAlive ?? undefined,
        searchString: query.query,

        sortByField: query.sortField ?? undefined,
        sortDirection: query.sortDirection ?? undefined,
        sortId: query.sortId ?? undefined,
        pageSize: query.pageSize ?? undefined,
    });
};

export const getFilesCount = async (
    query: Pick<SearchQuery, "id" | "keepAlive" | "query">,
): Promise<GetFilesCountResponse> => {
    return filesApi.getFilesCountV1FilesCountGet({
        queryId: query.id ?? undefined,
        keepAlive: query.keepAlive ?? undefined,
        searchString: query.query,
    });
};

export const searchTree = async (
    query: SearchQuery,
    childrenOfNode?: string,
    after?: string,
): Promise<GetFilesTreeResponse> => {
    return filesApi.getFilesTreeV1FilesTreeGet({
        queryId: query.id ?? undefined,
        keepAlive: query.keepAlive ?? undefined,
        searchString: query.query,
        nodePath: childrenOfNode,
        after,
    });
};

export const searchByFilename = async (
    query: PitBoundSearchQuery,
    filename: string,
    after?: SearchAfterCursor,
): Promise<SearchByFilenameResponse> => {
    return filesApi.searchByFilenameV1FilesSearchByFilenamePost({
        searchByFilenameRequest: {
            queryId: query.id,
            keepAlive: query.keepAlive ?? undefined,
            searchString: query.query,
            filename,
            after,
        },
    });
};

export const getTreeSpine = async (
    query: SearchQuery,
    fullPath: string,
): Promise<GetFilesTreeResponse> => {
    return filesApi.getFilesTreeSpineV1FilesTreeSpineGet({
        queryId: query.id ?? undefined,
        keepAlive: query.keepAlive ?? undefined,
        searchString: query.query,
        fullPath,
    });
};

export const getTermsStats = async (): Promise<AvailableStat[]> =>
    filesApi.getAvailableStatsByTypeV1FilesStatsRegistryTypeGet({
        registryType: "terms",
    });

export const getHistogramStats = async (): Promise<AvailableStat[]> =>
    filesApi.getAvailableStatsByTypeV1FilesStatsRegistryTypeGet({
        registryType: "histogram",
    });

export const getTermsStat = async (
    query: SearchQuery,
    stat: string,
    size?: number,
    signal?: AbortSignal,
): Promise<TermsStatisticsModel> => {
    return filesApi.getTermsStatsV1FilesStatsTermsStatGet(
        {
            stat,
            queryId: query.id ?? undefined,
            keepAlive: query.keepAlive ?? undefined,
            searchString: query.query,
            size,
        },
        { signal },
    );
};

export const getHistogramStat = async (
    query: SearchQuery,
    stat: string,
    groupBy: string,
    signal?: AbortSignal,
): Promise<GroupedHistogramStatisticsModel> => {
    return filesApi.getHistogramStatsGroupedV1FilesStatsHistogramStatGroupedGroupByGet(
        {
            stat,
            groupBy,
            queryId: query.id ?? undefined,
            keepAlive: query.keepAlive ?? undefined,
            searchString: query.query,
        },
        { signal },
    );
};

export const uploadFile = async (file: File): Promise<void> => {
    return filesApi.uploadFileV1FilesPost({
        file: file,
    });
};

export const updateFile = async (
    fileId: string,
    request: UpdateFileRequest,
): Promise<void> => {
    return filesApi.updateFileV1FilesFileIdPut({
        fileId: fileId,
        updateFileRequest: request,
    });
};

export const updateFiles = async (
    query: SearchQuery,
    request: UpdateFileRequest,
): Promise<void> => {
    return filesApi.updateFilesByQueryV1FilesPut({
        updateFilesRequest: {
            query: {
                queryId: query.id ?? undefined,
                keepAlive: query.keepAlive ?? undefined,
                searchString: query.query,
            },
            request: request,
        },
    });
};

export const deleteTagFromFile = async (
    fileId: string,
    tagName: string,
): Promise<void> => {
    return filesApi.deleteTagV1FilesFileIdTagsTagToRemoveDelete({
        fileId: fileId,
        tagToRemove: tagName,
    });
};

export const addTagsToFile = async (
    fileId: string,
    tagNames: string[],
): Promise<void> => {
    return filesApi.addTagsV1FilesFileIdTagsPost({
        fileId: fileId,
        addTagsRequest: {
            tags: tagNames,
        },
    });
};

export const addTagsToFiles = async (
    query: SearchQuery,
    tags: string[],
): Promise<void> => {
    return tagsApi.addTagsV1FilesTagsPost({
        addTagsByQueryRequest: {
            tags: tags,
            query: {
                queryId: query.id ?? undefined,
                keepAlive: query.keepAlive ?? undefined,
                searchString: query.query,
            },
        },
    });
};

export const deleteTagFromFiles = async (tagName: string): Promise<void> => {
    return tagsApi.deleteTagV1FilesTagsTagToDeleteDelete({
        tagToDelete: tagName,
    });
};

export const getFile = async (
    fileId: string,
    query: SearchQuery,
): Promise<GetFileResponse> => {
    return filesApi.getFileV1FilesFileIdGet({
        queryId: query.id ?? undefined,
        keepAlive: query.keepAlive ?? undefined,
        fileId: fileId,
        searchString: query.query,
    });
};

export const getPreviewFields = async (): Promise<PreviewField[]> =>
    filesApi.getPreviewFieldsV1FilesPreviewFieldsGet();

/**
 * Preview requests that have been sent and not yet answered.
 *
 * Two paths ask for the same preview and neither can see the other: the
 * prefetcher reaching ahead of the viewport, and the card's own in-view effect
 * when it mounts. Nothing is cached until the answer arrives, so under fast
 * scrolling every file was fetched twice - 583 requests for 293 files in one
 * pass down the list. A second asker now joins the request already open.
 */
const previewsInFlight = new Map<string, Promise<GetFilePreviewResponse>>();

export const getFilePreview = async (
    fileId: string,
    query: SearchQuery,
    fields?: string[],
): Promise<GetFilePreviewResponse> => {
    // Keyed on everything the response depends on: the same file under a
    // different query carries different highlights.
    const key = JSON.stringify([
        fileId,
        query.id ?? null,
        query.keepAlive ?? null,
        query.query,
        fields ?? null,
    ]);
    const open = previewsInFlight.get(key);
    if (open) return open;
    const request = filesApi
        .getFilePreviewV1FilesFileIdPreviewGet({
            queryId: query.id ?? undefined,
            keepAlive: query.keepAlive ?? undefined,
            fileId: fileId,
            searchString: query.query,
            fields: fields,
        })
        .finally(() => {
            previewsInFlight.delete(key);
        });
    previewsInFlight.set(key, request);
    return request;
};

export const scheduleArchiveCreation = async (
    query: SearchQuery,
    note?: string,
): Promise<ArchiveCreatedResponse> => {
    return archivesApi.createNewArchiveV1ArchivePost({
        archiveRequest: {
            query: {
                queryId: query.id ?? undefined,
                keepAlive: query.keepAlive ?? undefined,
                searchString: query.query,
            },
            note,
        },
    });
};

export const hideArchive = async (archiveId: string): Promise<void> => {
    return archivesApi.updateArchiveV1ArchiveArchiveIdPut({
        archiveId: archiveId,
        updateArchiveRequest: {
            hidden: true,
        },
    });
};

export const deleteArchive = async (archiveId: string): Promise<void> => {
    return archivesApi.deleteArchiveV1ArchiveArchiveIdDelete({
        archiveId: archiveId,
    });
};

export const scheduleFileTranslation = async (
    lang: string,
    query: SearchQuery,
): Promise<void> => {
    return translationApi.translateFilesOnDemandV1FilesTranslationPost({
        translateAllRequest: {
            lang: lang,
            query: {
                queryId: query.id ?? undefined,
                keepAlive: query.keepAlive ?? undefined,
                searchString: query.query,
            },
        },
    });
};

export const scheduleSingleFileTranslation = async (
    lang: string,
    fileId: string,
): Promise<void> => {
    return filesApi.translateFileV1FilesFileIdTranslatePost({
        fileId: fileId,
        translateFileRequest: {
            lang: lang,
        },
    });
};

export const scheduleSingleFileSummarization = async (
    fileId: string,
    systemPrompt?: string | null,
): Promise<void> => {
    return filesApi.summarizeFileV1FilesFileIdSummarizePost({
        fileId: fileId,
        summarizeFileRequest: {
            systemPrompt: systemPrompt ?? undefined,
        },
    });
};

export const scheduleSingleImageDescription = async (
    fileId: string,
    systemPrompt?: string | null,
): Promise<void> => {
    return filesApi.imageDescriptionV1FilesFileIdImageDescriptionPost({
        fileId: fileId,
        imageDescriptionFileRequest: {
            systemPrompt: systemPrompt ?? undefined,
        },
    });
};

export const scheduleImageDescriptionByQuery = async (
    query: SearchQuery,
    systemPrompt?: string | null,
): Promise<void> => {
    return imageDescriptionApi.describeImagesOnDemandV1FilesImageDescriptionPost(
        {
            imageDescriptionRequest: {
                query: {
                    queryId: query.id ?? undefined,
                    keepAlive: query.keepAlive ?? undefined,
                    searchString: query.query,
                },
                systemPrompt: systemPrompt ?? undefined,
            },
        },
    );
};

export const scheduleFileSummarization = async (
    query: SearchQuery,
    systemPrompt?: string | null,
): Promise<void> => {
    return summarizationApi.summarizeFilesOnDemandV1FilesSummarizationPost({
        summarizationRequest: {
            query: {
                queryId: query.id ?? undefined,
                keepAlive: query.keepAlive ?? undefined,
                searchString: query.query,
            },
            systemPrompt: systemPrompt ?? undefined,
        },
    });
};

export const scheduleFileIndexing = async (
    query: SearchQuery,
): Promise<void> => {
    return indexApi.indexFilesOnDemandV1FilesIndexPost({
        indexAllRequest: {
            query: {
                queryId: query.id ?? undefined,
                keepAlive: query.keepAlive ?? undefined,
                searchString: query.query,
            },
        },
    });
};

export const scheduleSingleFileIndexing = async (
    fileId: string,
): Promise<void> => {
    return filesApi.indexFileV1FilesFileIdIndexPost({
        fileId: fileId,
    });
};

export const createAiContext = async (): Promise<ContextCreateResponse> => {
    return aiApi.createContextV1AiPost();
};

export const listAiContexts = async (): Promise<ListContextsResponse> =>
    aiApi.listContextsV1AiGet();

export const getContextHistory = async (
    contextId: string,
    options?: { after?: number; pageSize?: number },
): Promise<ContextHistoryResponse> =>
    aiApi.getContextHistoryV1AiContextIdHistoryGet({
        contextId,
        after: options?.after,
        pageSize: options?.pageSize,
    });

export const deleteAiContext = async (contextId: string): Promise<void> =>
    aiApi.deleteContextV1AiContextIdDelete({ contextId });

export const setAiContextMode = async (
    contextId: string,
    mode: string,
): Promise<void> =>
    aiApi.updateModesV1AiContextIdModesPatch({
        contextId,
        modeUpdate: {
            mode: mode as ModeUpdate["mode"],
        },
    });
