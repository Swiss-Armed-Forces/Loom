import { SearchQuery } from "@features/common/utils/model";

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
    GroupedHistogramStatisticsModel,
    TermsStatisticsModel,
    GetFileResponse,
    GetFilePreviewResponse,
    ArchiveCreatedResponse,
    ContextCreateResponse,
    TreeNodeModel,
    GetQueryResponse,
    GetFilesCountResponse,
    UpdateFileRequest,
} from "./generated";

const filesApi = new FilesApi();
const translationApi = new TranslationApi();
const archivesApi = new ArchivesApi();
const indexApi = new IndexApi();
const summarizationApi = new SummarizationApi();
const tagsApi = new TagsApi();
const aiApi = new AiApi();
const imageDescriptionApi = new ImageDescriptionApi();

export const loadTags = async (): Promise<string[]> => {
    return tagsApi.getTagsV1FilesTagsGet();
};

export const loadSummarizationSystemPrompt = async (): Promise<string> => {
    return summarizationApi.getSystemPromptV1FilesSummarizationSystemPromptGet();
};

export const loadVisionSystemPrompt = async (): Promise<string> => {
    return imageDescriptionApi.getSystemPromptV1FilesImageDescriptionSystemPromptGet();
};

export const getShortRunningQuery = async (): Promise<GetQueryResponse> => {
    return filesApi.getQueryV1FilesQueryPost({ keepAlive: "10s" });
};

export const getLongRunningQuery = async (): Promise<GetQueryResponse> => {
    return filesApi.getQueryV1FilesQueryPost({ keepAlive: "30m" });
};

export const searchFiles = async (
    query: SearchQuery,
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
        queryId: query.id,
        keepAlive: query.keepAlive ?? undefined,
        searchString: query.query,
    });
};

export const searchTree = async (
    query: SearchQuery,
    childrenOfNode?: string,
    flat?: boolean,
): Promise<TreeNodeModel[]> => {
    return filesApi.getFilesTreeV1FilesTreeGet({
        queryId: query.id,
        keepAlive: query.keepAlive ?? undefined,
        searchString: query.query,

        nodePath: childrenOfNode,
        flat,
    });
};

export const getTreeLevelNodeLimit = async () => {
    return filesApi.getTreeMaxElementCountV1FilesTreeMaxElementCountGet({});
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
): Promise<TermsStatisticsModel> => {
    return filesApi.getTermsStatsV1FilesStatsTermsStatGet({
        stat,
        queryId: query.id,
        keepAlive: query.keepAlive ?? undefined,
        searchString: query.query,
        size,
    });
};

export const getHistogramStat = async (
    query: SearchQuery,
    stat: string,
    groupBy: string,
): Promise<GroupedHistogramStatisticsModel> => {
    return filesApi.getHistogramStatsGroupedV1FilesStatsHistogramStatGroupedGroupByGet(
        {
            stat,
            groupBy,
            queryId: query.id,
            keepAlive: query.keepAlive ?? undefined,
            searchString: query.query,
        },
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
                queryId: query.id,
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
                queryId: query.id,
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
        queryId: query.id,
        keepAlive: query.keepAlive ?? undefined,
        fileId: fileId,
        searchString: query.query,
    });
};

export const getFilePreview = async (
    fileId: string,
    query: SearchQuery,
): Promise<GetFilePreviewResponse> => {
    return filesApi.getFilePreviewV1FilesFileIdPreviewGet({
        queryId: query.id,
        keepAlive: query.keepAlive ?? undefined,
        fileId: fileId,
        searchString: query.query,
    });
};

export const scheduleArchiveCreation = async (
    query: SearchQuery,
): Promise<ArchiveCreatedResponse> => {
    return archivesApi.createNewArchiveV1ArchivePost({
        archiveRequest: {
            query: {
                queryId: query.id,
                keepAlive: query.keepAlive ?? undefined,
                searchString: query.query,
            },
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

export const scheduleFileTranslation = async (
    lang: string,
    query: SearchQuery,
): Promise<void> => {
    return translationApi.translateFilesOnDemandV1FilesTranslationPost({
        translateAllRequest: {
            lang: lang,
            query: {
                queryId: query.id,
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
                    queryId: query.id,
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
                queryId: query.id,
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
                queryId: query.id,
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

export const createAiContext = async (
    query: SearchQuery,
): Promise<ContextCreateResponse> => {
    return aiApi.createContextV1AiPost({
        _queryParameters: {
            queryId: query.id,
            keepAlive: query.keepAlive ?? undefined,
            searchString: query.query,
        },
    });
};

export const processQuestion = async (
    context: ContextCreateResponse,
    question: string,
): Promise<ContextCreateResponse> => {
    return aiApi.processQuestionV1AiContextIdProcessQuestionPost({
        contextId: context.contextId,
        processQuestionQuery: {
            question: question,
        },
    });
};
