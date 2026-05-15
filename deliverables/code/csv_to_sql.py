"""Generate SQL INSERT statements from CSV files.

The script supports two use cases:

1. Generic CSV -> INSERT statements for a single table.
2. Article 57 drug CSV -> normalized INSERT statements for `drug`,
   `active_substance`, and `drug_active_substance`.

The generated SQL is intended for a fresh schema load.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Iterable


def sql_quote(value: str | None) -> str:
    """Return a SQL string literal or NULL."""

    if value is None:
        return "NULL"

    text = str(value).strip()
    if text == "":
        return "NULL"

    escaped = text.replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def read_csv_rows(csv_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a CSV file and return headers plus rows."""

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV file {csv_path} has no header row")
        rows = [dict(row) for row in reader]
        return list(reader.fieldnames), rows


def parse_mapping(mapping_values: list[str] | None) -> list[tuple[str, str]]:
    """Parse CSV-to-SQL column mappings from CLI arguments."""

    if not mapping_values:
        return []

    parsed: list[tuple[str, str]] = []
    for item in mapping_values:
        if "=" not in item:
            raise ValueError(f"Invalid mapping {item!r}. Use CSV_NAME=SQL_NAME")
        csv_name, sql_name = item.split("=", 1)
        csv_name = csv_name.strip()
        sql_name = sql_name.strip()
        if not csv_name or not sql_name:
            raise ValueError(f"Invalid mapping {item!r}. Use CSV_NAME=SQL_NAME")
        parsed.append((csv_name, sql_name))
    return parsed


def render_insert(table: str, columns: Iterable[str], values: Iterable[str]) -> str:
    column_list = ", ".join(f"`{column}`" for column in columns)
    value_list = ", ".join(values)
    return f"INSERT INTO `{table}` ({column_list}) VALUES ({value_list});"


def write_generic_inserts(
    csv_path: Path,
    output_path: Path,
    table: str,
    mappings: list[tuple[str, str]],
) -> None:
    headers, rows = read_csv_rows(csv_path)

    if mappings:
        csv_columns = [csv_name for csv_name, _ in mappings]
        sql_columns = [sql_name for _, sql_name in mappings]
    else:
        csv_columns = headers
        sql_columns = headers

    missing = [column for column in csv_columns if column not in headers]
    if missing:
        raise ValueError(f"Missing columns in CSV file: {missing}")

    statements = ["START TRANSACTION;"]
    for row in rows:
        values = [sql_quote(row.get(column)) for column in csv_columns]
        statements.append(render_insert(table, sql_columns, values))
    statements.append("COMMIT;")

    output_path.write_text("\n".join(statements) + "\n", encoding="utf-8")


def split_active_substances(raw_value: str | None) -> list[str]:
    """Split an Article 57 active substance field into individual names."""

    if raw_value is None:
        return []

    text = raw_value.strip()
    if not text:
        return []

    parts = [part.strip() for part in re.split(r"\s*[|,]\s*", text) if part.strip()]
    return parts


def write_article57_inserts(csv_path: Path, output_path: Path) -> None:
    """Generate normalized INSERT statements for the Article 57 drug CSV."""

    headers, rows = read_csv_rows(csv_path)

    required = [
        "Product name",
        "Active substance",
        "Route of administration",
        "Product authorisation country",
        "Marketing authorisation holder",
        "Pharmacovigilance system master file location",
        "Pharmacovigilance enquiries email address",
        "Pharmacovigilance enquiries telephone number",
    ]
    missing = [column for column in required if column not in headers]
    if missing:
        raise ValueError(f"Missing required Article 57 columns: {missing}")

    substance_ids: OrderedDict[str, int] = OrderedDict()
    drug_rows: list[tuple[int, dict[str, str]]] = []
    relations: list[tuple[int, list[str]]] = []

    for index, row in enumerate(rows, start=1):
        drug_rows.append((index, row))
        substances = split_active_substances(row.get("Active substance"))
        relations.append((index, substances))
        for substance in substances:
            if substance not in substance_ids:
                substance_ids[substance] = len(substance_ids) + 1

    statements = ["START TRANSACTION;"]

    if drug_rows:
        drug_values = []
        for drug_id, row in drug_rows:
            drug_values.append(
                "(" + ", ".join(
                    [
                        str(drug_id),
                        sql_quote(row.get("Product name")),
                        sql_quote(row.get("Route of administration")),
                        sql_quote(row.get("Product authorisation country")),
                        sql_quote(row.get("Marketing authorisation holder")),
                        sql_quote(row.get("Pharmacovigilance system master file location")),
                        sql_quote(row.get("Pharmacovigilance enquiries email address")),
                        sql_quote(row.get("Pharmacovigilance enquiries telephone number")),
                    ]
                ) + ")"
            )
        statements.append(
            "INSERT INTO `drug` (`id`, `product_name`, `route_of_administration`, `product_authorisation_country`, `marketing_authorisation_holder`, `pharmacovigilance_master_file_location`, `pharmacovigilance_email`, `pharmacovigilance_phone`) VALUES\n"
            + ",\n".join(drug_values)
            + ";"
        )

    if substance_ids:
        substance_values = []
        for substance, substance_id in substance_ids.items():
            substance_values.append(f"({substance_id}, {sql_quote(substance)})")
        statements.append(
            "INSERT INTO `active_substance` (`id`, `name`) VALUES\n"
            + ",\n".join(substance_values)
            + ";"
        )

    relation_values: list[str] = []
    for drug_id, substances in relations:
        for substance in substances:
            relation_values.append(f"({drug_id}, {substance_ids[substance]})")

    if relation_values:
        statements.append(
            "INSERT INTO `drug_active_substance` (`drug_id`, `substance_id`) VALUES\n"
            + ",\n".join(relation_values)
            + ";"
        )

    statements.append("COMMIT;")
    output_path.write_text("\n".join(statements) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert CSV files into SQL INSERT statements."
    )
    parser.add_argument("input_csv", help="Path to the source CSV file")
    parser.add_argument("output_sql", help="Path to the output SQL file")
    parser.add_argument(
        "--table",
        help="Target SQL table for generic CSV conversion",
    )
    parser.add_argument(
        "--map",
        action="append",
        dest="mappings",
        help="Map a CSV column to a SQL column using CSV_NAME=SQL_NAME",
    )
    parser.add_argument(
        "--article57",
        action="store_true",
        help="Generate normalized inserts for the Article 57 drug CSV",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input_csv)
    output_path = Path(args.output_sql)

    try:
        if args.article57:
            write_article57_inserts(input_path, output_path)
        else:
            if not args.table:
                raise ValueError("--table is required unless --article57 is used")
            write_generic_inserts(
                input_path,
                output_path,
                args.table,
                parse_mapping(args.mappings),
            )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())