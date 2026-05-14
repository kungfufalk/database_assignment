"""Preprocessing helpers for dataset files.

Provides a small utility to convert an Excel file (with header row)
containing three columns into CSV.
"""
from __future__ import annotations

from typing import Iterable, Optional
import argparse
import sys


def excel_to_csv(input_excel: str, output_csv: str, sheet_name: Optional[str | int] = 0,
				 use_columns: Optional[Iterable[str]] = None) -> None:
	"""Convert an Excel worksheet to CSV.

	Assumes the first row of the sheet contains column names. If `use_columns`
	is provided it will select those columns (by name). Otherwise the first
	three columns are used.

	Raises:
		FileNotFoundError: if the input file is not found.
		ImportError: if required packages are missing.
		ValueError: if the sheet doesn't contain at least three columns or
					requested columns are missing.
	"""
	try:
		import pandas as pd
	except Exception as e:  # pragma: no cover - environment may lack pandas
		raise ImportError(
			"pandas is required to read Excel files. Install with: pip install pandas openpyxl"
		) from e

	try:
		df = pd.read_excel(input_excel, sheet_name=sheet_name, header=0)
	except FileNotFoundError:
		raise
	except Exception as e:  # more specific errors come from pandas
		raise

	if use_columns:
		missing = [c for c in use_columns if c not in df.columns]
		if missing:
			raise ValueError(f"Requested columns not found in sheet: {missing}")
		out_df = df.loc[:, list(use_columns)]
	else:
		if df.shape[1] < 3:
			raise ValueError("Input sheet must contain at least three columns")
		out_df = df.iloc[:, :3]

	out_df.to_csv(output_csv, index=False)


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
	p = argparse.ArgumentParser(description="Convert Excel (3 cols) to CSV")
	p.add_argument("input", help="Path to input Excel file")
	p.add_argument("output", help="Path to output CSV file")
	p.add_argument("--sheet", default=0, help="Sheet name or index (default: 0)")
	p.add_argument("--cols", help="Comma-separated column names to export (optional)")
	return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
	args = _parse_args(argv)
	cols = None
	if args.cols:
		cols = [c.strip() for c in args.cols.split(",") if c.strip()]

	try:
		excel_to_csv(args.input, args.output, sheet_name=args.sheet, use_columns=cols)
	except Exception as e:
		print(f"Error: {e}", file=sys.stderr)
		return 2
	print(f"Wrote {args.output}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())

