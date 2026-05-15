#!/usr/bin/env python3
"""Generate Article 57 load SQL for the Docker MariaDB container.

The script is intentionally hardcoded to this repository layout:

- source CSV: data_files/preprocessed/article-57-product-data_en.csv
- output SQL: lamp/init/article57_load.sql

The generated SQL is executed inside the MariaDB container by the
existing docker compose workflow.
"""

from __future__ import annotations

import csv
from collections import OrderedDict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = ROOT / "data_files" / "preprocessed" / "article-57-product-data_en.csv"
OUTPUT_SQL = ROOT / "lamp" / "init" / "article57_load.sql"
CHUNK_SIZE = 1000

CSV_COLUMNS = (
    "product_name",
    "active_substance",
    "route_of_administration",
    "product_authorisation_country",
    "marketing_authorisation_holder",
    "pharmacovigilance_system_master_file_location",
    "pharmacovigilance_enquiries_email_address",
    "pharmacovigilance_enquiries_telephone_number",
)

SQL_COLUMNS = (
    "id",
    "product_name",
    "route_of_administration",
    "product_authorisation_country",
    "marketing_authorisation_holder",
    "pharmacovigilance_master_file_location",
    "pharmacovigilance_email",
    "pharmacovigilance_phone",
)

MAX_LEN = {
    "product_name": 255,
    "route_of_administration": 255,
    "product_authorisation_country": 100,
    "marketing_authorisation_holder": 255,
    "pharmacovigilance_master_file_location": 255,
    "pharmacovigilance_email": 255,
    "pharmacovigilance_phone": 100,
    "active_substance": 255,
}


def normalize_header(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def find_column(fieldnames: list[str], target: str) -> str:
    normalized_target = normalize_header(target)
    for fieldname in fieldnames:
        if normalize_header(fieldname) == normalized_target:
            return fieldname
    raise ValueError(f"Column not found: {target}")


def sql_quote(value: str | None) -> str:
    if value is None:
        return "NULL"

    text = str(value).strip()
    if not text:
        return "NULL"

    escaped = text.replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def clamp(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    return text[:max_len]


def read_rows(csv_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV file {csv_path} has no header row")
        rows = [dict(row) for row in reader]
        return list(reader.fieldnames), rows


def chunked(items: list[str], chunk_size: int) -> list[list[str]]:
    return [items[index : index + chunk_size] for index in range(0, len(items), chunk_size)]


def build_insert_statement(table: str, columns: tuple[str, ...], rows: list[str]) -> str:
    column_list = ", ".join(f"`{column}`" for column in columns)
    return (
        f"INSERT INTO `{table}` ({column_list}) VALUES\n"
        + ",\n".join(rows)
        + ";"
    )


def build_load_sql() -> None:
    headers, rows = read_rows(INPUT_CSV)

    required = [find_column(headers, column) for column in CSV_COLUMNS]

    substance_names: OrderedDict[str, None] = OrderedDict()
    drug_values: list[str] = []
    relation_statements: list[str] = []

    for index, row in enumerate(rows, start=1):
        product_name = clamp(row.get(required[0]), MAX_LEN["product_name"])
        route = clamp(row.get(required[2]), MAX_LEN["route_of_administration"])
        country = clamp(row.get(required[3]), MAX_LEN["product_authorisation_country"])
        holder = clamp(row.get(required[4]), MAX_LEN["marketing_authorisation_holder"])
        pv_location = clamp(row.get(required[5]), MAX_LEN["pharmacovigilance_master_file_location"])
        pv_email = clamp(row.get(required[6]), MAX_LEN["pharmacovigilance_email"])
        pv_phone = clamp(row.get(required[7]), MAX_LEN["pharmacovigilance_phone"])
        substance_name = clamp(row.get(required[1]), MAX_LEN["active_substance"])

        if not product_name:
            continue

        if substance_name:
            substance_names[substance_name] = None

        drug_values.append(
            "(" + ", ".join(
                [
                    str(index),
                    sql_quote(product_name),
                    sql_quote(route),
                    sql_quote(country),
                    sql_quote(holder),
                    sql_quote(pv_location),
                    sql_quote(pv_email),
                    sql_quote(pv_phone),
                ]
            ) + ")"
        )

        if substance_name:
            relation_statements.append(
                "INSERT IGNORE INTO `drug_active_substance` (`drug_id`, `substance_id`) "
                f"SELECT {index}, `id` FROM `active_substance` WHERE `name` = {sql_quote(substance_name)};"
            )

    statements = ["START TRANSACTION;"]

    for drug_chunk in chunked(drug_values, CHUNK_SIZE):
        statements.append(build_insert_statement("drug", SQL_COLUMNS, drug_chunk))

    substance_rows = [f"({sql_quote(substance)})" for substance in substance_names.keys()]
    for substance_chunk in chunked(substance_rows, CHUNK_SIZE):
        statements.append(
            "INSERT IGNORE INTO `active_substance` (`name`) VALUES\n"
            + ",\n".join(substance_chunk)
            + ";"
        )

    statements.extend(relation_statements)

    statements.append("COMMIT;")
    OUTPUT_SQL.write_text("\n".join(statements) + "\n", encoding="utf-8")


def main() -> int:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing input CSV: {INPUT_CSV}")

    OUTPUT_SQL.parent.mkdir(parents=True, exist_ok=True)
    build_load_sql()
    print(f"Wrote {OUTPUT_SQL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())