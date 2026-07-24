export const TERMS_STAT_ORDER = [
    "extension",
    "tika_file_type",
    "magic_file_type",
    "tika_meta.content_type.keyword",
    "detected_language",
    "tika_language",
    "translations.language",
    "tika_meta.dc_creator.keyword",
    "tika_meta.dc_subject.keyword",
    "tika_meta.meta_last_author.keyword",
    "tika_meta.pdf_producer.keyword",
    "tika_meta.pdf_docinfo_creator_tool.keyword",
    "tika_meta.message_from.keyword",
    "tika_meta.message_from_email.keyword",
    "tika_meta.message_from_name.keyword",
    "tika_meta.message_to.keyword",
    "tika_meta.message_to_email.keyword",
    "tika_meta.message_to_name.keyword",
    "tika_meta.message_cc.keyword",
    "tika_meta.message_bcc.keyword",
    "source",
    "tags",
    "flagged",
    "seen",
    "is_spam",
    "tika_handled_by",
    "archives",
    "content_truncated",
    "attachments_skipped",
    "state",
    "failed_task_names",
    "retried_task_names",
    "successful_task_names",
];

export const DATE_STAT_ORDER = [
    "tika_meta.dcterms_created",
    "tika_meta.dcterms_modified",
    "tika_meta.pdf_docinfo_created",
    "tika_meta.pdf_docinfo_modified",
    "uploaded_datetime",
];

export const NUMBER_STAT_ORDER = [
    "size",
    "thumbnail_total_frames",
    "recursion_depth",
    "reindex_count",
];

export const DEFAULT_TERMS_STAT = TERMS_STAT_ORDER[0];
export const DEFAULT_HISTOGRAM_STAT = DATE_STAT_ORDER[0];
