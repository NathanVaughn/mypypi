import argparse

import app.main


def main(days: int) -> None:
    app.main.storage_backend.delete_older_than_days(days)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete old package files")
    parser.add_argument(
        "days", type=int, help="Delete files older than this number of days"
    )

    args = parser.parse_args()
    main(args.days)
