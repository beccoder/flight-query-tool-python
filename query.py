"""Running queries against the flight database."""
from validator import FIELD_NAMES, parse_datetime

STRING_KEYS = ("flight_id", "origin", "destination")
DATETIME_KEYS = ("departure_datetime", "arrival_datetime")
NUMBER_KEYS = ("price", "min_price")
ALLOWED_KEYS = set(STRING_KEYS) | set(DATETIME_KEYS) | set(NUMBER_KEYS) | {"sort_by", "order", "limit"}


def _is_number(value) -> bool:
    # bool is a subclass of int, but booleans are not numbers here.
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_valid_query(query) -> bool:
    """Return True if the query object follows the query rules."""
    if not isinstance(query, dict):
        return False
    for key, value in query.items():
        if key not in ALLOWED_KEYS:
            return False
        if key in STRING_KEYS and not isinstance(value, str):
            return False
        if key in DATETIME_KEYS and parse_datetime(value) is None:
            return False
        if key in NUMBER_KEYS and not _is_number(value):
            return False
        if key == "sort_by" and value not in FIELD_NAMES:
            return False
        if key == "order" and value not in ("asc", "desc"):
            return False
        if key == "limit" and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
            return False
    if "order" in query and "sort_by" not in query:
        return False
    return True


def _matches(flight: dict, query: dict) -> bool:
    """True if the flight passes every filter in the query (AND)."""
    for key in STRING_KEYS:
        if key in query and flight.get(key) != query[key]:
            return False
    # 'YYYY-MM-DD HH:MM' strings sort in time order, so string comparison is
    # enough; parse anyway so a record with an odd value never matches by luck.
    if "departure_datetime" in query:
        dep = parse_datetime(flight.get("departure_datetime"))
        if dep is None or dep < parse_datetime(query["departure_datetime"]):
            return False
    if "arrival_datetime" in query:
        arr = parse_datetime(flight.get("arrival_datetime"))
        if arr is None or arr > parse_datetime(query["arrival_datetime"]):
            return False
    price = flight.get("price")
    if "price" in query and not (_is_number(price) and price <= query["price"]):
        return False
    if "min_price" in query and not (_is_number(price) and price >= query["min_price"]):
        return False
    return True


def run_query(db: list[dict], query: dict) -> dict:
    """Return one response entry for one query object.

    Valid query:   {"query": query, "matches": [...]}
    Invalid query: {"query": query, "error": "INVALID_QUERY", "matches": []}
    """
    if not is_valid_query(query):
        return {"query": query, "error": "INVALID_QUERY", "matches": []}

    matches = [flight for flight in db if _matches(flight, query)]

    if "sort_by" in query:
        key = query["sort_by"]
        # sorted() is stable in both directions, so equal values keep
        # database order even with reverse=True.
        matches = sorted(matches, key=lambda f: f.get(key),
                         reverse=query.get("order", "asc") == "desc")

    if "limit" in query:
        matches = matches[:query["limit"]]

    return {"query": query, "matches": matches}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    """Accept one query object or a list of them; always return a list."""
    if isinstance(queries, dict):
        queries = [queries]
    return [run_query(db, q) for q in queries]
