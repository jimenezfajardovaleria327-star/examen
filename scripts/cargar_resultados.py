#!/usr/bin/env python3
import os
import sys
import time

import psycopg2


CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS resultados (
    product TEXT PRIMARY KEY,
    total_revenue NUMERIC(18, 2) NOT NULL CHECK (total_revenue >= 0),
    rank INTEGER NOT NULL UNIQUE CHECK (rank BETWEEN 1 AND 10)
)
"""


def load_results(input_path):
    with open(input_path, encoding="utf-8") as source:
        rows = []
        for line in source:
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 3:
                continue
            product, revenue, rank = fields
            rows.append((product, revenue, int(rank)))

    last_error = None
    for attempt in range(30):
        try:
            with psycopg2.connect(
                host=os.environ["DB_HOST"],
                port=os.environ.get("DB_PORT", "5432"),
                dbname=os.environ["DB_NAME"],
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASSWORD"],
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(CREATE_TABLE)
                    cursor.execute("DELETE FROM resultados")
                    if rows:
                        from psycopg2.extras import execute_values

                        execute_values(
                            cursor,
                            "INSERT INTO resultados (product, total_revenue, rank) VALUES %s",
                            rows,
                        )
            print(f"Cargados {len(rows)} resultados en PostgreSQL")
            return
        except psycopg2.OperationalError as error:
            last_error = error
            time.sleep(min(attempt + 1, 5))
    raise RuntimeError(f"No se pudo conectar a PostgreSQL: {last_error}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: cargar_resultados.py <part-00000>")
    load_results(sys.argv[1])