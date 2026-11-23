# Flight Schedule Parser and Query Tool

Graded Python lab (RTU, Programming Languages) by **Bekhzod Khudoyarov**, student ID **251ADB066**.

A command-line program that validates flight schedule CSV files, stores the
valid flights as a JSON database, logs invalid rows to `errors.log`, and runs
JSON queries against the database. Standard library only, Python 3.13.

## Files

| File | Contents |
| --- | --- |
| `flight_parser.py` | Entry point: `main(argv)`, argparse CLI, logging, response file; student constants |
| `validator.py` | `load_airports`, `validate_row` (checks 1–11 in order), `to_record` |
| `csv_loader.py` | `parse_files`: line handling, error messages, cross-file `DUPLICATE_FLIGHT` |
| `query.py` | `run_query`, `run_queries`: filters, sorting, limit, `INVALID_QUERY` |
| `AI_USAGE.md` | AI use disclosure |
| `data/` | Sample input (CSV files, airport list, queries) |
| `tests/` | Public test script and expected outputs (unchanged from the starter) |

## Usage

```
python flight_parser.py -i data/db.csv -a data/airports.txt
python flight_parser.py -d data/flights -a data/airports.txt -o out/db.json
python flight_parser.py -j db.json -q data/query.json -r out/
python flight_parser.py -i data/db.csv -a data/airports.txt -q data/query.json
```

| Argument | Meaning |
| --- | --- |
| `-i FILE` | Parse one CSV file |
| `-d FOLDER` | Parse every `*.csv` file in the folder (sorted, no sub-folders) |
| `-j FILE` | Load an existing JSON database |
| `-a FILE` | Airport list (required with `-i` / `-d`) |
| `-o FILE` | Database output path (default `db.json`; not allowed with `-j`) |
| `-q FILE` | Query file (one object or an array of objects) |
| `-r FOLDER` | Folder for the response file (default: current directory) |

Exit codes: `0` success, `1` runtime error (printed as `Error: ...` on
stderr), `2` usage error.

## Tests

```
python tests/run_public_tests.py
```

All 29 public tests (groups A–H) pass.
