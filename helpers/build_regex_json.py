#!/usr/bin/env python3

import dataclasses
import io
import json
import pathlib
import re
import sys
import zipfile

import pandas as pd  # pylint: disable=E0401
import requests


@dataclasses.dataclass
class DataRegex:
    name: str
    regex: str
    tags: list[str]
    field: str = "content"
    enabled: bool = True


def get_tag_from_name(name):
    tag = re.sub(r"\s+", "_", name)
    return tag


def load_first():
    url = "https://raw.githubusercontent.com/odomojuli/RegExAPI/master/regex.csv"
    df_csv = pd.read_csv(url)
    # strip headers
    df_csv = df_csv.rename(columns=lambda x: x.strip())
    # strop all cells
    df_obj = df_csv.select_dtypes(["object"])
    df_csv[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())

    for _, row in df_csv.iterrows():
        name = f"{row['Platform/API']}:{row['Key Type']}"
        name = name.lower()
        tag = get_tag_from_name(name)
        regex = row["Target Regular Expression"]
        yield DataRegex(name=name, regex=regex, tags=[tag])


def load_second():
    url = "https://github.com/l4yton/RegHex/archive/refs/heads/master.zip"
    master_zip = requests.get(url, timeout=10).content
    master_zip_fd = io.BytesIO(master_zip)
    with zipfile.ZipFile(master_zip_fd, "r", zipfile.ZIP_DEFLATED) as zfd:
        for json_file in zfd.namelist():
            if json_file.endswith(".json"):
                try:
                    name = pathlib.Path(json_file).stem.lower()
                    tag = get_tag_from_name(name)
                    regex_json = json.loads(zfd.read(json_file))
                    if "pattern" in regex_json:
                        yield DataRegex(
                            name=name,
                            regex=regex_json["pattern"],
                            tags=[tag],
                        )
                    if "patterns" in regex_json:
                        for i, regex in enumerate(regex_json["patterns"]):
                            yield DataRegex(
                                name=f"{name}_{i}",
                                regex=regex,
                                tags=[tag],
                            )
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    msg = (
                        "[!] Failed extracting regex from: "
                        f"{json_file}, "
                        f"Exception {exc}"
                    )
                    print(msg, file=sys.stderr)


def get_regexes():
    """Try compiling all."""
    for regex in list(load_first()) + list(load_second()):
        try:
            re.compile(regex.regex)
            yield regex
        except Exception as exc:  # pylint: disable=broad-exception-caught
            msg = (
                f"[!] Failed compiling: {regex.name}, "
                f"regex: {regex.regex}, "
                f"exception: {exc}"
            )
            print(msg, file=sys.stderr)


def write_regex_json():
    """Write: REGEX_JSON file"""

    class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            return super().default(o)

    regexes = list(get_regexes())
    print(json.dumps(regexes, indent=4, cls=EnhancedJSONEncoder))


if __name__ == "__main__":
    write_regex_json()
