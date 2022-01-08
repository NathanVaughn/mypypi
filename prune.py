import argparse

import app.main


def main(days: int, dry_run: bool) -> None:
    deleted = app.main.storage_backend.delete_older_than_days(days, dry_run)

    if dry_run:
        print(f"{len(deleted)} files would have been deleted")
    else:
        print(f"{len(deleted)} files were deleted")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete old package files")
    parser.add_argument(
        "days", type=int, help="Delete files older than this number of days"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Don't actually delete anything"
    )

    args = parser.parse_args()
    main(args.days, args.dry_run)
