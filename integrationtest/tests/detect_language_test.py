from uuid import uuid4

import pytest
from common.dependencies import get_celery_app, get_lazybytes_service
from common.file.file_repository import File
from worker.index_file.tasks.translate import (
    LanguageDetection,
    detect_language_system_one_task,
    translate_detect_language_task,
)

GET_TIMEOUT = 720

# Plain prose about nothing in particular, in each language the decision model has a
# member for. A decision model picks between descriptions of the languages, so a text
# whose subject is one country and whose language is another asks it which of the two
# the question means; what these cover is the detection path, not that answer.
DETECTION_TEXTS = [
    (
        "en",
        "This is an English text. It is written in the English language and uses "
        "English words and sentence structure. A few more lines follow, so that the "
        "detector has something to work with beyond a single sentence.",
    ),
    # spellchecker:off
    (
        "de",
        "Dies ist ein deutscher Text. Er wurde in der deutschen Sprache verfasst und "
        "beinhaltet deutsche Wörter sowie Struktur. Ich schreibe hier jetzt noch ein "
        "paar Worte, aber nur um die Spracherkennung ein bisschen besser zu testen.",
    ),
    # spellchecker:on
]


@pytest.mark.parametrize(
    "expected_language, text",
    DETECTION_TEXTS,
    ids=[lang for lang, _ in DETECTION_TEXTS],
)
def test_detect_language_system_one_task(expected_language: str, text: str):
    text_lazy = get_lazybytes_service().from_bytes(text.encode())

    result = (
        get_celery_app()
        .send_task(
            detect_language_system_one_task.name,
            args=[
                text_lazy,
                File(
                    full_name=expected_language,
                    source="",
                    sha256=str(uuid4()),
                    size=0,
                ),
            ],
        )
        .get(timeout=GET_TIMEOUT)
    )

    assert result[1][0].language == expected_language


@pytest.mark.skip(reason="Requires larger model")
def test_translate_detect_language_task_answers_an_unlisted_language():
    """The generative fallback, which is the only path that can answer `pl`.

    `LanguagesToDetect` has no Polish member, so the system-one pass cannot: this sends
    a detection the decision model declined and asserts the fallback picks it up.
    """
    text = """Szwajcaria to piękny kraj, ponieważ zachwyca majestatycznymi Alpami,
    krystalicznie czystymi jeziorami i malowniczymi miasteczkami.
    Można tu podziwiać niezwykłe widoki, spacerować po górskich szlakach
    i odpoczywać nad wodą. Uroku dodają jej także zadbane miasta, urokliwe
    wioski oraz zmieniające się wraz z porami roku krajobrazy.
    """

    text_lazy = get_lazybytes_service().from_bytes(text.encode())

    result = (
        get_celery_app()
        .send_task(
            translate_detect_language_task.name,
            args=[
                LanguageDetection(text_lazy, None),
                File(full_name="pl", source="", sha256=str(uuid4()), size=0),
            ],
        )
        .get(timeout=GET_TIMEOUT)
    )

    assert result[1][0].language == "pl"
