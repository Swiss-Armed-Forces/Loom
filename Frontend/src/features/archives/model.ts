export interface ArchiveMeta {
    short_name: string;
    query: string;
    extra: Record<string, unknown>;
    updated_datetime: string;
}

export interface ArchiveContent {
    state: string;
    size: number;
}

export interface Archive {
    meta: ArchiveMeta;
    content: ArchiveContent;
    sha256: string;
    sha256_encrypted: string;
    hidden: boolean;
    file_id: string;
}

export interface ArchivesModel {
    clean: boolean;
    hits: Archive[];
    total: number;
    found: number;
    searchQuery: string;
    hasMore: boolean;
    currentPage: number;
}
