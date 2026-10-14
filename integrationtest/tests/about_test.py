from pathlib import Path

import requests
import yaml
from api.routers.about import AboutInfo

from utils.consts import ABOUT_ENDPOINT, REQUEST_TIMEOUT

CHART_FILE = Path(__file__).parents[2] / "charts" / "Chart.yaml"


def test_about_reports_the_deployed_chart_metadata():
    """The API must report the chart that deployed it.

    This is the only check that the settings ConfigMap keys and the pydantic field
    names still agree: a rename on either side leaves the defaults in place, which
    reads as a healthy API serving the wrong version.
    """
    chart = yaml.safe_load(CHART_FILE.read_text(encoding="utf-8"))

    response = requests.get(ABOUT_ENDPOINT, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    about = AboutInfo.model_validate(response.json())

    assert about.name == chart["name"]
    assert about.version == chart["version"]
    assert about.app_version == chart["appVersion"]
    assert about.description == chart["description"]
