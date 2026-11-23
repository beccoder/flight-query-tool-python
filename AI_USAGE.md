# AI Usage Disclosure

**Student:** Bekhzod Khudoyarov (251ADB066)
**Assignment:** Graded lab: Flight query tool in Python

## Tools used

- **Claude Code** (Anthropic's command-line coding agent), model **Claude Opus 5.5** (`claude-opus-5-5`), November 2026.

## Conversation links

- The work was done in a local Claude Code terminal session. Claude Code CLI
  sessions do not generate a public share URL, so there is no link to paste.
  The full session transcript is stored locally and I can show it on request.

## What I used them for

- Reading the assignment PDF and the starter README, then summarising the
  specification rules (CLI arguments, the 12 validation checks in priority
  order, exit codes, error log format, and query schema/filtering rules).
- Drafting initial implementations and structure across the four modules from
  the starter skeletons so I could review, test, and refine them against the
  specification.
- Explaining tricky edge cases and verifying my assumptions: why
  `str.isalnum()`, `\d`, and `datetime.strptime` alone are not strict enough
  for ASCII/format requirements, how Python's `sorted(..., reverse=True)`
  preserves relative order on ties (Timsort stability), and why `bool` must
  be explicitly excluded when validating numeric fields.
- Explaining the `logging` handler lifecycle (`try`/`finally`, removing and
  closing the handler) and how to prevent `argparse` from terminating the
  process via `sys.exit()` when `main(argv)` is invoked repeatedly in tests.
- Running the public test suite and verifying additional edge cases (missing
  airport file, non-UTF-8 CSV input, missing `-r` directory, query arrays
  containing non-object elements, `-h`, and price edge cases such as `inf`
  and scientific notation like `1e3`).
- Drafting and refining this disclosure (`AI_USAGE.md`) and `README.md` to
  accurately document my workflow and design decisions.

## Which parts of the code were AI-generated or substantially AI-assisted

| File | Function or part | How (generated / modified / explained) |
| --- | --- | --- |
| `validator.py` | `load_airports`, `validate_row`, `to_record`, `parse_datetime`, the ASCII regexes | Drafted with AI assistance, then reviewed and verified line by line against every check in the spec |
| `csv_loader.py` | `parse_files`, `_physical_lines`, `_split` | Drafted with AI assistance; 1-based physical line numbering (`\n` / `\r\n`, headers, blank lines, and `#` comments) was explained and verified |
| `query.py` | `is_valid_query`, `_matches`, `run_query`, `run_queries` | Drafted with AI assistance, then verified against the specification's worked examples and edge cases |
| `flight_parser.py` | `main`, `build_parser`, `parse_args`, `parse_and_store`, loaders, `write_response` | Drafted with AI assistance; student constants, CLI behavior, and `logging` cleanup were verified |
| `README.md`, `AI_USAGE.md` | Whole files | Drafted with AI assistance, then reviewed and edited by me |

## Key prompts

Below are the main prompts I used during the session, written to clarify
requirements, test my understanding of edge cases, and verify my solution
against the specification.

1. **Specification walkthrough and initial draft prompt:**
   > Read the assignment PDF and `flight-lab-starter.zip` carefully, then
   > walk me through the exact requirements before writing code—covering CLI
   > flags, exit codes, error logging, query rules, and the 12 validation
   > checks in order. After that, help draft initial implementations for the
   > four modules matching the starter signatures so I can review and test
   > each part against the spec.

2. **Validation rules and strict edge-case verification prompt:**
   > Let's review `validator.py` against the spec and verify subtle edge
   > cases. `validate_row` receives raw `csv.reader` fields (unstripped) and
   > must return the first failing code in order: `WRONG_FIELD_COUNT`,
   > `MISSING_FIELD`, `INVALID_FLIGHT_ID` (strict ASCII `^[A-Za-z0-9]{2,8}$`),
   > `INVALID_ORIGIN` / `INVALID_DESTINATION` (3 uppercase ASCII letters and
   > present in the airport set), `SAME_ORIGIN_DESTINATION`,
   > `INVALID_DEPARTURE` / `INVALID_ARRIVAL` (exact zero-padded
   > `YYYY-MM-DD HH:MM` representing a valid calendar date/time, avoiding
   > `strptime` leniency like `2025-1-5 9:3`), `ARRIVAL_NOT_AFTER_DEPARTURE`,
   > `INVALID_PRICE` (`float()` failure or `nan`/`inf`), and
   > `NON_POSITIVE_PRICE`. Duplicate detection should not happen here. Keep it
   > standard-library-only and silent on import, and explain any non-obvious
   > regex or date-parsing pitfalls.

3. **Physical line tracking, CLI handling, and logging lifecycle prompt:**
   > Help me verify `csv_loader.py` and `flight_parser.py`. In `parse_files`,
   > line numbers must be 1-based physical lines (including headers, blank
   > lines, and `#` comments) across both `\n` and `\r\n`, formatted as
   > `<base name>:<line>: <CODE> | <original line>`, with `DUPLICATE_FLIGHT`
   > checked across files on `(flight_id, departure_datetime)` using only
   > previously valid rows. For `main(argv)` with `argparse`, enforce mutually
   > exclusive `-i`/`-d`/`-j` (exit code `2` on invalid CLI usage), require
   > `-a` for `-i`/`-d`, disallow `-o` with `-j` via `parser.error`, and
   > return exit codes instead of calling `sys.exit()`. Runtime errors must
   > print a single `Error: ...` line to `stderr` without a traceback and
   > return `1`. Also explain how to manage the `errors.log` file handler
   > (`logging`, no `basicConfig`, removed and closed in `finally`) so repeated
   > `main()` calls in a single test process stay clean.

4. **Query semantics, edge cases, and test verification prompt:**
   > Let's check `query.py` and output generation against the spec. Filters
   > combine with logical AND: exact match for `flight_id`, `origin`, and
   > `destination`; `departure` >= filter value; `arrival` <= filter value;
   > `price` <= filter value; `min_price` >= filter value. Verify stable
   > sorting (including `desc`), `order` requiring `sort_by`, and non-negative
   > integer `limit` applied after sorting. Unknown keys, wrong types,
   > booleans treated as numbers, invalid datetimes, negative `limit`, or
   > `order` without `sort_by` must produce
   > `{"query": q, "error": "INVALID_QUERY", "matches": []}`. Confirm the
   > output filename format `response_<ID>_<FIRST>_<LAST>_<YYYYMMDD_HHMM>.json`
   > for student `251ADB066` (Bekhzod Khudoyarov), then run
   > `tests/run_public_tests.py` and help me inspect any failures or edge
   > cases.

## What I changed or verified myself

I set my student constants, ran `python tests/run_public_tests.py` (all 29
tests in groups A–H pass), and manually tested additional edge cases
(missing airport file, non-UTF-8 input, missing `-r` folder, `-h`, and
prices such as `inf` and `1e3`). I also read through every function and
checked each validation and query rule against the assignment specification so
I can explain and defend the implementation during the exam.

```