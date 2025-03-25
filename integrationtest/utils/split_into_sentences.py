# from: https://stackoverflow.com/a/31505798

import re

ALPHABETS = r"([A-Za-z])"
PREFIXES = r"(Mr|St|Mrs|Ms|Dr)[.]"
SUFFIXES = r"(Inc|Ltd|Jr|Sr|Co)"
STARTERS = (
    r"(Mr|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt"
    r"|He\s|She\s|It\s|They\s|Their\s"
    r"|Our\s|We\s|But\s|However\s|That\s"
    r"|This\s|Wherever)"
)
ACRONYMS = r"([A-Z][.][A-Z][.](?:[A-Z][.])?)"
WEBSITES = r"[.](com|net|org|io|gov|edu|me)"
DIGITS = r"([0-9])"
MULTIPLE_DOTS = r"\.{2,}"


def split_into_sentences(text: str) -> list[str]:
    """Split the text into sentences.

    If the text contains substrings "<prd>" or "<stop>", they would lead to incorrect
    splitting because they are used as markers for splitting.

    :param text: text to be split into sentences
    :type text: str
    :return: list of sentences
    :rtype: list[str]
    """
    text = " " + text + "  "
    text = text.replace("\n", " ")
    text = re.sub(PREFIXES, "\\1<prd>", text)
    text = re.sub(WEBSITES, "<prd>\\1", text)
    text = re.sub(DIGITS + "[.]" + DIGITS, "\\1<prd>\\2", text)
    text = re.sub(
        MULTIPLE_DOTS, lambda match: "<prd>" * len(match.group(0)) + "<stop>", text
    )
    if "Ph.D" in text:
        text = text.replace("Ph.D.", "Ph<prd>D<prd>")
    text = re.sub(r"\s" + ALPHABETS + "[.] ", " \\1<prd> ", text)
    text = re.sub(ACRONYMS + " " + STARTERS, "\\1<stop> \\2", text)
    text = re.sub(
        ALPHABETS + "[.]" + ALPHABETS + "[.]" + ALPHABETS + "[.]",
        "\\1<prd>\\2<prd>\\3<prd>",
        text,
    )
    text = re.sub(ALPHABETS + "[.]" + ALPHABETS + "[.]", "\\1<prd>\\2<prd>", text)
    text = re.sub(" " + SUFFIXES + "[.] " + STARTERS, " \\1<stop> \\2", text)
    text = re.sub(" " + SUFFIXES + "[.]", " \\1<prd>", text)
    text = re.sub(" " + ALPHABETS + "[.]", " \\1<prd>", text)
    if "”" in text:
        text = text.replace(".”", "”.")
    if '"' in text:
        text = text.replace('."', '".')
    if "!" in text:
        text = text.replace('!"', '"!')
    if "?" in text:
        text = text.replace('?"', '"?')
    text = text.replace(".", ".<stop>")
    text = text.replace("?", "?<stop>")
    text = text.replace("!", "!<stop>")
    text = text.replace("<prd>", ".")
    sentences = text.split("<stop>")
    sentences = [s.strip() for s in sentences]
    if sentences and not sentences[-1]:
        sentences = sentences[:-1]
    return sentences
