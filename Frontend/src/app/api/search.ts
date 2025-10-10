import { SearchQuery } from "../../features/search/model";
import {
    AiApi,
    ArchivesApi,
    FilesApi,
    IndexApi,
    SummarizationApi,
    TagsApi,
    TranslationApi,
    LibretranslateSupportedLanguages,
    GetFilesResponse,
    SummaryStatisticsModel,
    Stat,
    GenericStatisticsModel,
    FileUploadResponse,
    GetFileResponse,
    GetFilePreviewResponse,
    ArchiveCreatedResponse,
    ContextCreateResponse,
    TreeNodeModel,
    GetQueryResponse,
    GetFilesCountResponse,
} from "./generated";

const filesApi = new FilesApi();
const translationApi = new TranslationApi();
const archivesApi = new ArchivesApi();
const indexApi = new IndexApi();
const summarizationApi = new SummarizationApi();
const tagsApi = new TagsApi();
const aiApi = new AiApi();

export const loadTags = async (): Promise<string[]> => {
    return tagsApi.getTagsV1FilesTagsGet();
};

export const loadLanguages = async (): Promise<
    LibretranslateSupportedLanguages[]
> => {
    return translationApi.getSupportedLanguagesV1FilesTranslationLanguagesGet();
};

export const loadSummarizationSystemPrompt = async (): Promise<string> => {
    return summarizationApi.getSystemPromptV1FilesSummarizationSystemPromptGet();
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
        languages: query.languages?.map((l) => l.code),
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
): Promise<TreeNodeModel[]> => {
    return filesApi.getFilesTreeV1FilesTreeGet({
        queryId: query.id,
        keepAlive: query.keepAlive ?? undefined,
        searchString: query.query,
        languages: query.languages?.map((l) => l.code),
        nodePath: childrenOfNode,
    });
};

export const getTreeLevelNodeLimit = async () => {
    return filesApi.getTreeMaxElementCountV1FilesTreeMaxElementCountGet({});
};

export const getStatSummary = async (
    query: SearchQuery,
): Promise<SummaryStatisticsModel> => {
    return filesApi.getSummaryStatsV1FilesStatsSummaryGet({
        queryId: query.id,
        keepAlive: query.keepAlive ?? undefined,
        searchString: query.query,
        languages: query.languages?.map((l) => l.code),
    });
};

export const getStatGeneric = async (
    query: SearchQuery,
    stat: Stat,
): Promise<GenericStatisticsModel> => {
    return filesApi.getGenericStatsV1FilesStatsGenericStatGet({
        stat,
        queryId: query.id,
        keepAlive: query.keepAlive ?? undefined,
        searchString: query.query,
        languages: query.languages?.map((l) => l.code),
    });
};

export const uploadFile = async (file: File): Promise<FileUploadResponse> => {
    return filesApi.uploadFileV1FilesPost({
        file: file,
    });
};

export const updateFile = async (
    fileId: string,
    hidden: boolean,
): Promise<void> => {
    return filesApi.updateFileV1FilesFileIdPut({
        fileId: fileId,
        updateFileRequest: {
            hidden: hidden,
        },
    });
};

export const updateFiles = async (
    query: SearchQuery,
    hidden: boolean,
): Promise<void> => {
    return filesApi.updateFilesByQueryV1FilesPut({
        updateFilesRequest: {
            query: {
                queryId: query.id,
                keepAlive: query.keepAlive ?? undefined,
                searchString: query.query,
                languages: query.languages?.map((l) => l.code),
            },
            hidden: hidden,
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

export const addTagToFile = async (
    fileId: string,
    tagName: string,
): Promise<void> => {
    return filesApi.addTagV1FilesFileIdTagsTagToAddPost({
        fileId: fileId,
        tagToAdd: tagName,
    });
};

export const addTagsToFiles = async (
    query: SearchQuery,
    tags: string[],
): Promise<void> => {
    return tagsApi.addTagsV1FilesTagsPost({
        addTagRequest: {
            tags: tags,
            query: {
                queryId: query.id,
                keepAlive: query.keepAlive ?? undefined,
                searchString: query.query,
                languages: query.languages?.map((l) => l.code),
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
        languages: query.languages?.map((l) => l.code),
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
        languages: query.languages?.map((l) => l.code),
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
                languages: query.languages?.map((l) => l.code),
            },
        },
    });
};

export const hideArchive = async (archiveId: string): Promise<void> => {
    return archivesApi.updateArchiveV1ArchiveArchiveIdPost({
        archiveId: archiveId,
        updateArchiveModel: {
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
                languages: query.languages?.map((l) => l.code),
            },
        },
    });
};

export const scheduleSingleFileTranslation = async (
    lang: string,
    file_id: string,
): Promise<void> => {
    return filesApi.translateFileV1FilesFileIdTranslatePost({
        fileId: file_id,
        translateFileRequest: {
            lang: lang,
        },
    });
};

export const scheduleSingleFileSummarization = async (
    file_id: string,
    systemPrompt?: string | null,
): Promise<void> => {
    return filesApi.summarizeFileV1FilesFileIdSummarizePost({
        fileId: file_id,
        summarizeFileRequest: {
            systemPrompt: systemPrompt ?? undefined,
        },
    });
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
                languages: query.languages?.map((l) => l.code),
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
                languages: query.languages?.map((l) => l.code),
            },
        },
    });
};

export const scheduleSingleFileIndexing = async (
    file_id: string,
): Promise<void> => {
    return filesApi.indexFileV1FilesFileIdIndexPost({
        fileId: file_id,
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
            languages: query.languages?.map((l) => l.code),
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
