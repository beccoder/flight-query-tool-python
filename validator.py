"""Row validation: airport list loading, single-row checks, record building."""
import math
import re
from datetime import datetime

FIELD_NAMES = (
    "flight_id",
    "origin",
    "destination",
    "departure_datetime",
    "arrival_datetime",
    "price",
)

DATETIME_FORMAT = "%Y-%m-%d %H:%M"

# Explicit ASCII character classes: \d and str.isalnum() would also accept
# non-ASCII digits and letters, which the specification forbids.
_FLIGHT_ID_RE = re.compile(r"[A-Za-z0-9]{2,8}")
_AIRPORT_RE = re.compile(r"[A-Z]{3}")
_DATETIME_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}")


def parse_datetime(value: str) -> datetime | None:
    """Return a datetime for an exact 'YYYY-MM-DD HH:MM' string, else None.

    The regular expression enforces the exact shape (zero padding, single
    space, 24-hour clock); strptime then rejects impossible dates such as
    2025-02-30 or 24:00. strptime alone is not enough because it accepts
    '2025-1-5 9:3'.
    """
    if not isinstance(value, str) or not _DATETIME_RE.fullmatch(value):
        return None
    try:
        return datetime.strptime(value, DATETIME_FORMAT)
    except ValueError:
        return None


def load_airports(path: str) -> set[str]:
    """Read an airport list file and return the set of codes.

    One code per line. Strip whitespace; skip blank lines and lines
    starting with '#'.
    """
    codes = set()
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            code = line.strip()
            if not code or code.startswith("#"):
                continue
            codes.add(code)
    return codes


def _valid_airport(code: str, airports: set[str]) -> bool:
    return bool(_AIRPORT_RE.fullmatch(code)) and code in airports


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    """Check one CSV row (fields as returned by csv.reader, not yet stripped).

    Return None if the row is valid, otherwise the error code of the
    FIRST failing check (checks 1-11 in the specification, in order).
    Does not check for duplicates.
    """
    # 1. exactly six fields
    if len(fields) != len(FIELD_NAMES):
        return "WRONG_FIELD_COUNT"

    flight_id, origin, destination, dep, arr, price = (f.strip() for f in fields)

    # 2. no empty field
    if not all((flight_id, origin, destination, dep, arr, price)):
        return "MISSING_FIELD"

    # 3. flight id: 2-8 ASCII letters or digits
    if not _FLIGHT_ID_RE.fullmatch(flight_id):
        return "INVALID_FLIGHT_ID"

    # 4-5. airports: 3 uppercase ASCII letters and present in the list
    if not _valid_airport(origin, airports):
        return "INVALID_ORIGIN"
    if not _valid_airport(destination, airports):
        return "INVALID_DESTINATION"

    # 6. origin and destination differ
    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"

    # 7-9. date and time values
    dep_dt = parse_datetime(dep)
    if dep_dt is None:
        return "INVALID_DEPARTURE"
    arr_dt = parse_datetime(arr)
    if arr_dt is None:
        return "INVALID_ARRIVAL"
    if arr_dt <= dep_dt:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    # 10-11. price
    try:
        value = float(price)
    except ValueError:
        return "INVALID_PRICE"
    if not math.isfinite(value):
        return "INVALID_PRICE"
    if value <= 0:
        return "NON_POSITIVE_PRICE"

    return None


def to_record(fields: list[str]) -> dict:
    """Turn a valid row into a flight record dictionary.

    Keys: flight_id, origin, destination, departure_datetime,
    arrival_datetime (stripped strings) and price (float).
    """
    values = [f.strip() for f in fields]
    record = dict(zip(FIELD_NAMES, values))
    record["price"] = float(record["price"])
    return record
