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
)
from common.models.base_repository import BaseRepository
from common.utils.object_id_str import ObjectIdStr

from worker.utils.persister_base import PersisterBase


# pylint: disable=too-many-public-methods
class IndexingPersister(PersisterBase[File]):
    """Persists the results of the indexing tasks Has to be used in a `with
    IndexingPersister(file_id) as x:` statement to ensure that the file is saved."""

    @classmethod
    def get_repository(cls) -> BaseRepository[File]:
        repository = get_file_repository()
        return repository

    def set_thumbnail_file_id(self, thumbnail_file_id: ObjectIdStr):
        self._object.thumbnail_file_id = thumbnail_file_id

    def set_thumbnail_total_frames(self, thumbnail_total_frames: int):
        self._object.thumbnail_total_frames = thumbnail_total_frames

    def set_rendered_file_image_file_id(self, rendered_file_image_file_id: ObjectIdStr):
        self._object.rendered_file.image_file_id = rendered_file_image_file_id

    def set_rendered_file_office_pdf_file_id(
        self, rendered_file_office_pdf_file_id: ObjectIdStr
    ):
        self._object.rendered_file.office_pdf_file_id = rendered_file_office_pdf_file_id

    def set_rendered_file_browser_pdf_file_id(
        self, rendered_file_browser_pdf_file_id: ObjectIdStr
    ):
        self._object.rendered_file.browser_pdf_file_id = (
            rendered_file_browser_pdf_file_id
        )

    def set_state(self, state: str):
        self._object.state = state

    def set_content(self, content: str):
        self._object.content = content

    def set_content_truncated(self, content_truncated: bool):
        self._object.content_truncated = content_truncated

    def set_magic_file_type(self, file_type: str):
        self._object.magic_file_type = file_type

    def set_tika_file_type(self, file_type: str):
        self._object.tika_file_type = file_type

    def set_tika_language(self, language: str):
        self._object.tika_language = language

    def set_libretranslate_language(self, language: str):
        self._object.libretranslate_language = language

    def add_or_replace_libretranslate_translated_language(
        self, libretranslate_translated_language: LibretranslateTranslatedLanguage
    ):
        # remove filter previous translation
        filtered_translations = LibreTranslateTranslations(
            translation
            for translation in self._object.libretranslate_translations
            if translation.language != libretranslate_translated_language.language
        )
        self._object.libretranslate_translations = filtered_translations
        # add new translation
        self._object.libretranslate_translations.append(
            libretranslate_translated_language
        )

    def set_tika_meta(self, meta: dict):
        self._object.tika_meta = meta

    def set_is_spam(self, is_spam: bool):
        self._object.is_spam = is_spam

    def set_imap_info(self, imap_info: ImapInfo):
        self._object.imap = imap_info

    def add_or_replace_attachment(self, attachment: Attachment):
        # remove previous attachment with same name
        filtered_attachments = [
            att for att in self._object.attachments if att.name != attachment.name
        ]
        self._object.attachments = filtered_attachments
        # add new attachment
        self._object.attachments.append(attachment)

    def add_archive(self, archive_id: UUID):
        self._object.archives.append(str(archive_id))

    def set_hidden_state_file(self, hidden: bool):
        self._object.hidden = hidden

    def add_tag(self, tag: Tag):
        if tag not in self._object.tags:
            self._object.tags.append(tag)

    def remove_tag(self, tag: Tag):
        self._object.tags.remove(tag)

    def set_summary(self, summary: str):
        self._object.summary = summary

    def set_embeddings(self, embeddings: list[Embedding]):
        self._object.embeddings = embeddings

    def set_ripsecrets_secret(self, secrets: list[Secret]):
        self._object.ripsecrets_secrets = secrets

    def set_trufflehog_secret(self, secrets: list[Secret]):
        self._object.trufflehog_secrets = secrets
