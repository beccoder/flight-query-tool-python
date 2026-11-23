"""Flight Schedule Parser and Query Tool - command-line entry point.

Run from the project folder, for example:
    python flight_parser.py -i data/db.csv -a data/airports.txt
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

STUDENT_ID = "251ADB066"
FIRST_NAME = "Bekhzod"
LAST_NAME = "Khudoyarov"

LOGGER_NAME = "flight_parser"


class AppError(Exception):
    """An expected runtime problem: reported as 'Error: ...', exit code 1."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flight_parser.py",
        description="Validate flight schedule CSV files, store valid flights "
                    "as a JSON database and run queries against it.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-i", metavar="FILE", help="parse a single CSV file")
    source.add_argument("-d", metavar="FOLDER", help="parse every .csv file in a folder")
    source.add_argument("-j", metavar="FILE", help="load an existing JSON database")
    parser.add_argument("-a", metavar="FILE", help="airport list file (required with -i and -d)")
    parser.add_argument("-o", metavar="FILE", help="output path for the JSON database (default: db.json)")
    parser.add_argument("-q", metavar="FILE", help="JSON file with queries to run")
    parser.add_argument("-r", metavar="FOLDER", default=".",
                        help="folder for the query response file (default: current directory)")
    return parser


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.j is not None:
        if args.o is not None:
            parser.error("argument -o: not allowed with argument -j")
    elif args.a is None:
        parser.error("argument -a is required with -i and -d")
    return args


# ------------------------------------------------------------------ helpers

def read_json(path: str, what: str):
    if not os.path.isfile(path):
        raise AppError(f"{what} '{path}' does not exist")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise AppError(f"{what} '{path}' is not valid JSON: {exc}") from None
    except OSError as exc:
        raise AppError(f"cannot read {what} '{path}': {exc.strerror or exc}") from None


def load_database(path: str) -> list[dict]:
    data = read_json(path, "JSON database")
    if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
        raise AppError(f"JSON database '{path}' must be an array of objects")
    return data


def load_queries(path: str) -> dict | list:
    data = read_json(path, "query file")
    if isinstance(data, dict):
        return data
    if isinstance(data, list) and all(isinstance(q, dict) for q in data):
        return data
    raise AppError(f"query file '{path}' must contain a query object or an array of query objects")


def csv_paths(args: argparse.Namespace) -> list[str]:
    """The CSV files to parse, in processing order."""
    if args.i is not None:
        if not os.path.isfile(args.i):
            raise AppError(f"CSV file '{args.i}' does not exist or is not a file")
        return [args.i]
    if not os.path.isdir(args.d):
        raise AppError(f"folder '{args.d}' does not exist or is not a folder")
    try:
        names = sorted(os.listdir(args.d))
    except OSError as exc:
        raise AppError(f"cannot read folder '{args.d}': {exc.strerror or exc}") from None
    paths = [os.path.join(args.d, n) for n in names
             if n.endswith(".csv") and os.path.isfile(os.path.join(args.d, n))]
    if not paths:
        raise AppError(f"folder '{args.d}' contains no .csv files")
    return paths


def write_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def parse_and_store(args: argparse.Namespace, logger: logging.Logger) -> list[dict]:
    """Parse the CSV input, write the database and errors.log, return the records."""
    paths = csv_paths(args)
    if not os.path.isfile(args.a):
        raise AppError(f"airport list '{args.a}' does not exist")
    airports = load_airports(args.a)

    db_path = args.o if args.o is not None else "db.json"
    log_path = os.path.join(os.path.dirname(db_path), "errors.log")

    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
    try:
        try:
            records, errors = parse_files(paths, airports)
        except UnicodeDecodeError as exc:
            logger.error("input is not valid UTF-8: %s", exc)
            raise AppError(f"input file is not valid UTF-8: {exc}") from None
        for message in errors:
            logger.warning(message)
        logger.info("parsed %d file(s): %d valid row(s), %d invalid row(s)",
                    len(paths), len(records), len(errors))
    finally:
        logger.removeHandler(handler)
        handler.close()

    write_json(db_path, records)
    print(f"{len(records)} valid flight(s) written to {db_path}, "
          f"{len(errors)} invalid row(s) logged to {log_path}")
    return records


def write_response(folder: str, responses: list[dict]) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    name = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{stamp}.json"
    path = os.path.join(folder, name)
    write_json(path, responses)
    return path


# ------------------------------------------------------------------ main

def main(argv: list[str] | None = None) -> int:
    """Run the whole program and return the exit code (0, 1 or 2).

    argv is the argument list without the program name.
    None means use sys.argv[1:] (argparse does this for you).
    """
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        # argparse exits with 2 on usage errors and 0 for -h; return instead.
        return exc.code if isinstance(exc.code, int) else 2

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    try:
        # Read the query file first so a bad one fails before any output.
        queries = load_queries(args.q) if args.q is not None else None

        if args.j is not None:
            db = load_database(args.j)
        else:
            db = parse_and_store(args, logger)

        if queries is not None:
            if not os.path.isdir(args.r):
                raise AppError(f"response folder '{args.r}' does not exist")
            path = write_response(args.r, run_queries(db, queries))
            print(f"query responses written to {path}")
        return 0
    except AppError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        name = f" '{exc.filename}'" if exc.filename else ""
        print(f"Error: cannot access{name}: {exc.strerror or exc}", file=sys.stderr)
        return 1
    except UnicodeDecodeError as exc:
        print(f"Error: file is not valid UTF-8: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
