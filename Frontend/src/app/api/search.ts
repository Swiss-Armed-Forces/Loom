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

export const searchFiles = async (
    query: SearchQuery,
): Promise<GetFilesResponse> => {
    return filesApi.getFilesV1FilesGet({
        searchString: query.query ?? "",
        languages: query.languages?.map((l) => l.code),
        ...(query.sortField && {
            sortByField: query.sortField,
        }),
        ...(query.sortDirection && {
            sortDirection: query.sortDirection,
        }),
        ...(query.sortId && {
            sortId: query.sortId,
        }),
        ...(query.pageSize != null && {
            pageSize: query.pageSize,
        }),
    });
};
export const searchTree = async (
    query: SearchQuery,
    childrenOfNode?: string,
): Promise<TreeNodeModel[]> => {
    return filesApi.getFilesTreeV1FilesTreeGet({
        searchString: query.query ?? "",
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
    if (!query.query || query.query.trim().length === 0) {
        return { count: 0, min: 0, max: 0, avg: 0 };
    }

    return filesApi.getSummaryStatsV1FilesStatsSummaryGet({
        searchString: query.query ?? "",
        languages: query.languages?.map((l) => l.code),
    });
};

export const getStatGeneric = async (
    query: SearchQuery,
    stat: Stat,
): Promise<GenericStatisticsModel> => {
    if (!query.query || query.query.trim().length === 0) {
        return { stat: "", key: "", data: [], fileCount: 0 };
    }

    return filesApi.getGenericStatsV1FilesStatsGenericStatNameGet({
        searchString: query.query ?? "",
        languages: query.languages?.map((l) => l.code),
        statName: stat,
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
                searchString: query.query ?? "",
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
                searchString: query.query ?? "",
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

export const getFullFileContent = async (
    fileId: string,
    query: SearchQuery,
): Promise<GetFileResponse> => {
    return filesApi.getFileV1FilesFileIdGet({
        fileId: fileId,
        searchString: query.query ?? "",
        languages: query.languages?.map((l) => l.code),
    });
};

export const getFilePreview = async (
    fileId: string,
    query: SearchQuery,
): Promise<GetFilePreviewResponse> => {
    return filesApi.getFilePreviewV1FilesFileIdPreviewGet({
        fileId: fileId,
        searchString: query.query ?? "",
        languages: query.languages?.map((l) => l.code),
    });
};

export const scheduleArchiveCreation = async (
    query: SearchQuery,
): Promise<ArchiveCreatedResponse> => {
    return archivesApi.createNewArchiveV1ArchivePost({
        archiveRequest: {
            query: {
                searchString: query.query ?? "",
                languages: query.languages?.map((l) => l.code) ?? [],
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
                searchString: query.query ?? "",
                languages: query.languages?.map((l) => l.code) ?? [],
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
                searchString: query.query ?? "",
                languages: query.languages?.map((l) => l.code) ?? [],
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
                searchString: query.query ?? "",
                languages: query.languages?.map((l) => l.code) ?? [],
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
        searchString: query.query ?? undefined,
        languages: query.languages ?? undefined,
    });
};

export const processQuestion = async (
    context: ContextCreateResponse,
    question: string,
): Promise<ContextCreateResponse> => {
    return aiApi.processQuestionV1AiContextIdProcessQuestionPost({
        contextId: context.contextId,
        question: question,
    });
};
