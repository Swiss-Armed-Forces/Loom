from enum import IntEnum, StrEnum
from typing import Annotated

from pydantic import BaseModel, Field
from pydantic_ai import UseEnumMemberDocstrings


class ImageDescriptionResult(BaseModel):
    description: str


class ElasticsearchQuery(BaseModel):
    query_string: str


class TranslationResult(BaseModel):
    text: str


class DetectedLanguage(BaseModel, frozen=True):
    confidence: Annotated[
        float,
        Field(ge=0, le=100),
    ]
    language: str


class SummarizationResult(BaseModel):
    text: str


# The languages a decision model picks between. The member docstrings reach the service
# as the description of each option, so they are the only thing telling it what an
# option covers. `other` is the one whose meaning is not its own label, and the one the
# callers branch on.
#
# The class docstring is the question this enum is asked as a bare output type, and is
# what a wrapping model's field description stands in for. Either way it reaches the
# service, so it holds the question and nothing else.
class LanguagesToDetect(UseEnumMemberDocstrings, StrEnum):
    """In which language is this text written?"""

    EN = "en"
    """The text is written in English."""

    DE = "de"
    """The text is written in German."""

    FR = "fr"
    """The text is written in French."""

    IT = "it"
    """The text is written in Italian."""

    OTHER = "other"
    """The text is in none of the languages above, or carries no language signal."""


# A model rather than the bare enum, because the caller reads the whole distribution
# back out of `provider_details["probabilities"]` and that mapping is keyed by output
# *field* name. A bare output type is wrapped by pydantic-ai under a name of its own
# choosing, which nothing here would notice changing; a field named below is a name
# this package owns.
#
# The class carries no docstring: pydantic-ai sends one to the service as the goal the
# question is asked for, where anything but what the model should read is noise around
# the question.
class DetectedLanguageChoice(BaseModel):
    language: LanguagesToDetect = Field(
        description="In which language is this text written?"
    )


LANGUAGE_PROBABILITIES_FIELD = next(iter(DetectedLanguageChoice.model_fields))
"""The key `DetectedLanguageChoice`'s distribution is reported under.

Read off the model rather than written out, so renaming the field renames the lookup
with it.
"""


class IndexingUrgency(UseEnumMemberDocstrings, IntEnum):
    """How soon is the content of this document worth reading?"""

    LOW = 0
    """The name suggests nothing worth reading: a program, a resource bundle, a media
    file, or a document far too large to be correspondence."""

    MEDIUM = 1
    """The name suggests a document that may carry information, or says too little
    about the content to tell."""

    HIGH = 2
    """The name suggests correspondence or a document carrying information -- an .eml,
    .pdf or .docx -- at a size that reads like one, at most several MB."""


# The rerank scale. The member docstrings are the whole rubric sent to the model:
# pydantic-ai's schema generation turns them into the enum's descriptions, so they are
# the only thing telling it what each number means.
#
# The class docstring is the question, as it is for `LanguagesToDetect` above.
class Relevance(UseEnumMemberDocstrings, IntEnum):
    """How relevant is the document to the question?"""

    COMPLETELY_IRRELEVANT = 0
    """The document is completely irrelevant to the question."""

    IRRELEVANT = 1
    """The document is irrelevant to the question."""

    SLIGHTLY_RELEVANT = 2
    """The document is slightly relevant to the question."""

    SOMEWHAT_RELEVANT = 3
    """The document is somewhat relevant to the question."""

    RELEVANT = 4
    """The document is relevant to the question."""

    VERY_RELEVANT = 5
    """The document is very relevant to the question."""


class RerankResult(BaseModel):
    rank: Relevance = Field(
        description="How well does the document answer the question?"
    )
