"""Run the scheduled retention maintenance job.

Usage from the backend directory:
    python -m scripts.run_retention          # report only
    python -m scripts.run_retention --apply  # delete eligible rows
"""

import argparse
import json

from app.core.database import SessionLocal
from app.services.data_retention import run_retention


def main() -> int:
    parser = argparse.ArgumentParser(description="Run EpiSphere retention maintenance")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="delete eligible rows; without this flag the run is a dry-run",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = run_retention(db, dry_run=not args.apply)
        db.commit()
        print(json.dumps(result.as_dict(), sort_keys=True))
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
