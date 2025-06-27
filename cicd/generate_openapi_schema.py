#!/usr/bin/env python3
import json
from api.api import init_api


def main() -> None:
    app = init_api()
    print(json.dumps(app.openapi()))


if __name__ == "__main__":
    main()
