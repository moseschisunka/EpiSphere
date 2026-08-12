"""Export the FastAPI OpenAPI document for client contract verification."""

import argparse
import json
from pathlib import Path
import sys

BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIRECTORY))

from app.main import app


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the EpiSphere OpenAPI document")
    parser.add_argument("output", type=Path, help="Path to the JSON output file")
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
