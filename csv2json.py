#!/usr/bin/env python3
"""CSV2JSON v1.0.0 -- Zero-dependency CSV to JSON batch converter.

Converts CSV files into clean, type-aware JSON. Supports single files,
batch directory processing, stdin piping, and type auto-detection.
Author: Wang Jian Wei  |  License: MIT
"""

import argparse, csv, json, os, re, sys
from pathlib import Path

__version__ = "1.0.0"


def infer_type(value: str):
    """Convert CSV cell to best-fit Python type (int/float/bool/null/str)."""
    if not value:
        return ""
    s = value.strip() or ""
    if not s:
        return ""
    lo = s.lower()
    if lo in ("null", "none", "nil"):
        return None
    if lo == "true":
        return True
    if lo == "false":
        return False
    if re.match(r"^[+-]?\d+$", s):
        try:
            return int(s)
        except ValueError:
            pass
    if re.match(r"^[+-]?\d*\.?\d+(?:[eE][+-]?\d+)?$", s):
        try:
            return float(s)
        except ValueError:
            pass
    return s


def convert_csv_to_json(
    input_path: str, output_path: str | None = None,
    delimiter: str = ",", encoding: str = "utf-8",
    no_type_infer: bool = False, pretty: bool = True,
    skip_bad_rows: bool = False, encoding_errors: str = "replace",
) -> int:
    """Convert one CSV to JSON. Returns record count, or -1 on error."""
    rows: list[dict] = []
    in_file = None
    try:
        if input_path == "-":
            reader = csv.DictReader(sys.stdin, delimiter=delimiter)
            src = "<stdin>"
        else:
            in_file = open(input_path, "r", encoding=encoding,
                           errors=encoding_errors, newline="")
            reader = csv.DictReader(in_file, delimiter=delimiter)
            src = input_path
        if not reader.fieldnames:
            print(f"Error: No headers in '{src}'. File empty?", file=sys.stderr)
            return -1
        for ln, row in enumerate(reader, start=2):
            try:
                if None in row.values() and None in row.keys():
                    continue
                processed = {}
                for k, v in row.items():
                    if k is None:
                        continue
                    processed[k] = v if no_type_infer else infer_type(v)
                rows.append(processed)
            except Exception as exc:
                msg = f"Warning: Bad row line {ln} in '{src}': {exc}"
                if skip_bad_rows:
                    print(msg, file=sys.stderr)
                    continue
                print(msg, file=sys.stderr)
                return -1
    except FileNotFoundError:
        print(f"Error: File not found '{input_path}'", file=sys.stderr)
        return -1
    except UnicodeDecodeError as exc:
        print(f"Error: Encoding issue '{input_path}' "
              f"(current: {encoding}). {exc}", file=sys.stderr)
        return -1
    except Exception as exc:
        print(f"Error: {src}: {exc}", file=sys.stderr)
        return -1
    finally:
        if in_file:
            in_file.close()
    out = json.dumps(rows, ensure_ascii=False,
                     indent=2 if pretty else None, default=str)
    if output_path:
        try:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(out)
                if not out.endswith("\n"):
                    f.write("\n")
            print(f"OK  {len(rows)} records  ->  {output_path}", file=sys.stderr)
        except OSError as exc:
            print(f"Error: Cannot write '{output_path}': {exc}", file=sys.stderr)
            return -1
    else:
        sys.stdout.write(out)
        if pretty:
            sys.stdout.write("\n")
        sys.stdout.flush()
    return len(rows)


def batch_convert(
    input_dir: str, output_dir: str,
    delimiter: str = ",", encoding: str = "utf-8",
    no_type_infer: bool = False, pretty: bool = True,
    skip_bad_rows: bool = False, encoding_errors: str = "replace",
) -> tuple[int, int]:
    """Convert all *.csv in a directory. Returns (success, fail)."""
    in_dir = Path(input_dir)
    if not in_dir.is_dir():
        print(f"Error: '{input_dir}' is not a directory.", file=sys.stderr)
        return 0, 1
    csv_files = sorted(in_dir.glob("*.csv"))
    if not csv_files:
        print(f"Warning: No .csv files in '{input_dir}'", file=sys.stderr)
        return 0, 0
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ok = bad = 0
    for f in csv_files:
        rc = convert_csv_to_json(
            input_path=str(f),
            output_path=str(out_dir / (f.stem + ".json")),
            delimiter=delimiter, encoding=encoding,
            no_type_infer=no_type_infer, pretty=pretty,
            skip_bad_rows=skip_bad_rows, encoding_errors=encoding_errors,
        )
        if rc >= 0:
            ok += 1
        else:
            bad += 1
    return ok, bad


def main() -> None:
    p = argparse.ArgumentParser(
        prog="csv2json",
        description="Convert CSV files to clean, type-aware JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="examples:\n"
        "  csv2json data.csv                     stdout (pretty-print)\n"
        "  csv2json data.csv -o out.json         save to file\n"
        "  csv2json data.csv --compact           minified output\n"
        "  csv2json data.csv --no-infer          keep all fields as strings\n"
        "  csv2json data.csv -d \";\"             semicolon delimiter\n"
        "  csv2json -i ./csv/ -o ./json/         batch convert directory\n"
        "  cat data.csv | csv2json -             read from stdin\n"
        "  csv2json data.csv --encoding gbk      GBK (Chinese) encoding\n")
    p.add_argument("input", nargs="?", default=None,
                   help="CSV file path, or '-' for stdin")
    p.add_argument("-o", "--output", default=None,
                   help="Output JSON path (default: stdout)")
    p.add_argument("-i", "--input-dir", default=None,
                   help="Input directory for batch mode (*.csv)")
    p.add_argument("-d", "--delimiter", default=",",
                   help="Field delimiter (default: ',')")
    p.add_argument("--encoding", default="utf-8",
                   help="Input encoding (utf-8, gbk, latin-1, utf-16, …)")
    p.add_argument("--no-infer", action="store_true",
                   help="Disable type inference; keep all fields as strings")
    p.add_argument("--compact", action="store_true",
                   help="Minified JSON (no indentation)")
    p.add_argument("--skip-bad-rows", action="store_true",
                   help="Skip malformed rows instead of aborting")
    p.add_argument("--encoding-errors", default="replace",
                   choices=["strict", "replace", "ignore"],
                   help="How to handle encoding errors (default: replace)")
    p.add_argument("--version", action="version",
                   version=f"csv2json v{__version__}")
    args = p.parse_args()

    if args.input_dir:
        if not args.output:
            print("Error: -o/--output required in batch mode.", file=sys.stderr)
            sys.exit(1)
        ok, bad = batch_convert(
            input_dir=args.input_dir, output_dir=args.output,
            delimiter=args.delimiter, encoding=args.encoding,
            no_type_infer=args.no_infer, pretty=not args.compact,
            skip_bad_rows=args.skip_bad_rows,
            encoding_errors=args.encoding_errors,
        )
        print(f"\nDone: {ok}/{ok + bad} OK, {bad} failed.", file=sys.stderr)
        sys.exit(0 if bad == 0 else 1)

    if not args.input:
        p.print_help()
        sys.exit(1)

    rc = convert_csv_to_json(
        input_path=args.input, output_path=args.output,
        delimiter=args.delimiter, encoding=args.encoding,
        no_type_infer=args.no_infer, pretty=not args.compact,
        skip_bad_rows=args.skip_bad_rows,
        encoding_errors=args.encoding_errors,
    )
    sys.exit(0 if rc >= 0 else 1)

if __name__ == "__main__":
    main()