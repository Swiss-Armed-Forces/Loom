import { ArchivesApi, ArchivesModel } from ".";

const archivesApi = new ArchivesApi();

export const getAll = async (): Promise<ArchivesModel> => {
    return archivesApi.getAllArchivesV1ArchiveGet();
};
