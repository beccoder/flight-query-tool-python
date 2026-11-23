"""Reading CSV files into flight records and error messages."""
import csv
import os

from validator import to_record, validate_row


def _physical_lines(path: str) -> list[str]:
    """Return the file's physical lines without their line endings.

    The file is read with newline="" so that no newline translation happens,
    then split on '\\n' only and a trailing '\\r' is removed. This handles
    both '\\n' and '\\r\\n' endings and keeps line numbers exact
    (str.splitlines() would also split on other characters such as '\\x0c').
    A UTF-8 byte order mark, if present, is dropped.
    """
    with open(path, encoding="utf-8-sig", newline="") as f:
        text = f.read()
    lines = text.split("\n")
    return [line[:-1] if line.endswith("\r") else line for line in lines]


def _split(line: str) -> list[str]:
    """Split one line into fields with the csv module."""
    try:
        return next(csv.reader([line]), [])
    except csv.Error:
        # A malformed line (e.g. a stray NUL byte) cannot have six fields.
        return []


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    """Process the CSV files in the order given.

    Return (records, errors):
      records - valid flight records, in input order
      errors  - one message per invalid row, in input order, formatted as
                "<file name>:<line number>: <ERROR_CODE> | <free text>"
                (base file name only, no timestamp or level, no newline)

    Also performs the DUPLICATE_FLIGHT check across all the files.
    Does not write any files and does not log anything itself.
    """
    records: list[dict] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()  # (flight_id, departure_datetime) of valid rows

    for path in paths:
        name = os.path.basename(path)
        for number, line in enumerate(_physical_lines(path), start=1):
            if number == 1:
                continue  # header
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue  # blank or comment line

            fields = _split(line)
            code = validate_row(fields, airports)
            if code is None:
                record = to_record(fields)
                key = (record["flight_id"], record["departure_datetime"])
                if key in seen:
                    code = "DUPLICATE_FLIGHT"
                else:
                    seen.add(key)
                    records.append(record)

            if code is not None:
                errors.append(f"{name}:{number}: {code} | {line}")

    return records, errors
