from uuid import UUID

from common.dependencies import get_file_repository
from common.file.file_repository import (
    Attachment,
    Embedding,
    File,
    ImapInfo,
    LibretranslateTranslatedLanguage,
    LibreTranslateTranslations,
    Secret,
    Tag,
    TikaMeta,
)
from common.models.base_repository import BaseRepository
from common.services.lazybytes_service import LazyBytes

from worker.utils.persister_base import PersisterBase, mutation


# Module-level mutation functions
def _set_thumbnail_data(obj: File, thumbnail_data: LazyBytes) -> None:
    obj.thumbnail_data = thumbnail_data


def _set_thumbnail_total_frames(obj: File, thumbnail_total_frames: int) -> None:
    obj.thumbnail_total_frames = thumbnail_total_frames


def _set_rendered_file_image_data(
    obj: File, rendered_file_image_data: LazyBytes
) -> None:
    obj.rendered_file.image_data = rendered_file_image_data


def _set_rendered_file_office_pdf_data(
    obj: File, rendered_file_office_pdf_data: LazyBytes
) -> None:
    obj.rendered_file.office_pdf_data = rendered_file_office_pdf_data


def _set_rendered_file_browser_pdf_data(
    obj: File, rendered_file_browser_pdf_data: LazyBytes
) -> None:
    obj.rendered_file.browser_pdf_data = rendered_file_browser_pdf_data


def _set_state(obj: File, state: str) -> None:
    obj.state = state


def _set_content(obj: File, content: str) -> None:
    obj.content = content


def _set_content_truncated(obj: File, content_truncated: bool) -> None:
    obj.content_truncated = content_truncated


def _set_magic_file_type(obj: File, file_type: str) -> None:
    obj.magic_file_type = file_type


def _set_tika_file_type(obj: File, file_type: str) -> None:
    obj.tika_file_type = file_type


def _set_tika_language(obj: File, language: str) -> None:
    obj.tika_language = language


def _set_libretranslate_language(obj: File, language: str) -> None:
    obj.libretranslate_language = language


def _add_or_replace_libretranslate_translated_language(
    obj: File, libretranslate_translated_language: LibretranslateTranslatedLanguage
) -> None:
    # remove filter previous translation
    filtered_translations = LibreTranslateTranslations(
        translation
        for translation in obj.libretranslate_translations
        if translation.language != libretranslate_translated_language.language
    )
    obj.libretranslate_translations = filtered_translations
    # add new translation
    obj.libretranslate_translations.append(libretranslate_translated_language)


def _set_tika_meta(obj: File, meta: TikaMeta) -> None:
    obj.tika_meta = meta


def _set_tika_handled_by(obj: File, handled_by: str) -> None:
    obj.tika_handled_by = handled_by


def _set_is_spam(obj: File, is_spam: bool) -> None:
    obj.is_spam = is_spam


def _set_imap_info(obj: File, imap_info: ImapInfo) -> None:
    obj.imap = imap_info


def _add_or_replace_attachment(obj: File, attachment: Attachment) -> None:
    # remove previous attachment with same name
    filtered_attachments = [
        att for att in obj.attachments if att.name != attachment.name
    ]
    obj.attachments = filtered_attachments
    # add new attachment
    obj.attachments.append(attachment)


def _add_archive(obj: File, archive_id: UUID) -> None:
    obj.archives.append(str(archive_id))


def _set_hidden_state_file(obj: File, hidden: bool) -> None:
    obj.hidden = hidden


def _add_tag(obj: File, tag: Tag) -> None:
    if tag not in obj.tags:
        obj.tags.append(tag)


def _remove_tag(obj: File, tag: Tag) -> None:
    obj.tags.remove(tag)


def _set_summary(obj: File, summary: str) -> None:
    obj.summary = summary


def _set_embeddings(obj: File, embeddings: list[Embedding]) -> None:
    obj.embeddings = embeddings


def _set_ripsecrets_secret(obj: File, secrets: list[Secret]) -> None:
    obj.ripsecrets_secrets = secrets


def _set_trufflehog_secret(obj: File, secrets: list[Secret]) -> None:
    obj.trufflehog_secrets = secrets


# pylint: disable=too-many-public-methods
class IndexingPersister(PersisterBase[File]):
    """Persists the results of the indexing tasks."""

    @classmethod
    def get_repository(cls) -> BaseRepository[File]:
        repository = get_file_repository()
        return repository

    # Bind mutations as class attributes
    set_thumbnail_data = mutation(_set_thumbnail_data)
    set_thumbnail_total_frames = mutation(_set_thumbnail_total_frames)
    set_rendered_file_image_data = mutation(_set_rendered_file_image_data)
    set_rendered_file_office_pdf_data = mutation(_set_rendered_file_office_pdf_data)
    set_rendered_file_browser_pdf_data = mutation(_set_rendered_file_browser_pdf_data)
    set_state = mutation(_set_state)
    set_content = mutation(_set_content)
    set_content_truncated = mutation(_set_content_truncated)
    set_magic_file_type = mutation(_set_magic_file_type)
    set_tika_file_type = mutation(_set_tika_file_type)
    set_tika_language = mutation(_set_tika_language)
    set_libretranslate_language = mutation(_set_libretranslate_language)
    add_or_replace_libretranslate_translated_language = mutation(
        _add_or_replace_libretranslate_translated_language
    )
    set_tika_meta = mutation(_set_tika_meta)
    set_tika_handled_by = mutation(_set_tika_handled_by)
    set_is_spam = mutation(_set_is_spam)
    set_imap_info = mutation(_set_imap_info)
    add_or_replace_attachment = mutation(_add_or_replace_attachment)
    add_archive = mutation(_add_archive)
    set_hidden_state_file = mutation(_set_hidden_state_file)
    add_tag = mutation(_add_tag)
    remove_tag = mutation(_remove_tag)
    set_summary = mutation(_set_summary)
    set_embeddings = mutation(_set_embeddings)
    set_ripsecrets_secret = mutation(_set_ripsecrets_secret)
    set_trufflehog_secret = mutation(_set_trufflehog_secret)
