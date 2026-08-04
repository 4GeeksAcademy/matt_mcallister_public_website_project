"""
Safe snippet for basic pandas cleaning. Copy and adapt for your dataset.
Run: python pandas_clean.py  (ensure pandas is installed)
"""
import sys
from pathlib import Path

import pandas as pd


DEBUG_MODE = "--debug" in sys.argv


def debug_print(*args, **kwargs) -> None:
	if DEBUG_MODE:
		print(*args, **kwargs)


def main() -> int:
	data_path = Path("data.csv")

	if not data_path.exists():
		print(f"ERROR: Input file not found: {data_path}", file=sys.stderr)
		return 1

	try:
		df = pd.read_csv(data_path)
	except FileNotFoundError:
		print("ERROR: Input file was not found.", file=sys.stderr)
		return 1
	except PermissionError:
		print("ERROR: Permission denied while reading the input file.", file=sys.stderr)
		return 1
	except pd.errors.ParserError:
		print("ERROR: The CSV file could not be parsed. Check its format.", file=sys.stderr)
		return 1
	except OSError:
		print("ERROR: An I/O error occurred while reading the input file.", file=sys.stderr)
		return 1

	if df.empty:
		print("ERROR: Input dataset is empty. Nothing to process.", file=sys.stderr)
		return 1

	debug_print("df_shape", df.shape)
	debug_print("df_dtypes", df.dtypes)

	try:
		df = df.dropna(axis=1, how="all")
	except (TypeError, ValueError):
		print("ERROR: Failed while removing empty columns.", file=sys.stderr)
		return 1

	debug_print("df_shape_after_drop_all_null_cols", df.shape)

	try:
		df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
	except (AttributeError, TypeError):
		print("ERROR: Failed while normalising column names.", file=sys.stderr)
		return 1

	debug_print("df_columns", list(df.columns))

	try:
		before = len(df)
		df = df.drop_duplicates()
		debug_print("rows_dropped_duplicates", before - len(df))
	except (TypeError, ValueError):
		print("ERROR: Failed while removing duplicate rows.", file=sys.stderr)
		return 1

	debug_print("df_head", df.head())

	return 0


if __name__ == "__main__":
	sys.exit(main())
