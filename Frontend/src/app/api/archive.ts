import { apiConfiguration } from "./apiConfiguration";

import { ArchivesApi, ArchivesModel } from ".";

const archivesApi = new ArchivesApi(apiConfiguration);

export const getAll = async (): Promise<ArchivesModel> => {
    return archivesApi.getAllArchivesV1ArchiveGet();
};

export const getEncryptionKey = async (): Promise<string | null> => {
    const response =
        await archivesApi.getEncryptionKeyV1ArchiveEncryptionKeyGet();
    return response.encryptionKey ?? null;
};

export const importArchive = async (file: File): Promise<void> => {
    await archivesApi.importArchiveV1ArchiveImportPost({ file });
};
