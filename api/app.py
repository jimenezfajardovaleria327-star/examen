import os
import subprocess
import time
from decimal import Decimal, InvalidOperation

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request


app = Flask(__name__)


def get_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def serialize(row):
    return {
        "product": row["product"],
        "total_revenue": float(row["total_revenue"]),
        "rank": row["rank"],
    }


def parse_result_payload(payload, include_rank=False):
    if not isinstance(payload, dict) or not str(payload.get("product", "")).strip():
        raise ValueError("product es obligatorio")
    try:
        revenue = Decimal(str(payload["total_revenue"]))
        if not revenue.is_finite() or revenue < 0:
            raise ValueError
    except (KeyError, InvalidOperation, ValueError):
        raise ValueError("total_revenue debe ser un numero no negativo") from None

    values = [str(payload["product"]).strip(), revenue]
    if include_rank:
        try:
            rank = int(payload["rank"])
            if rank < 1 or rank > 10:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            raise ValueError("rank debe ser un entero entre 1 y 10") from None
        values.append(rank)
    return values


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/resultados")
def get_results():
    with get_connection() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT product, total_revenue, rank FROM resultados ORDER BY rank, product")
        return jsonify([serialize(row) for row in cursor.fetchall()])


@app.get("/resultados/<path:product>")
def get_result(product):
    with get_connection() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            "SELECT product, total_revenue, rank FROM resultados WHERE product = %s",
            (product,),
        )
        row = cursor.fetchone()
    if row is None:
        return jsonify(error="resultado no encontrado"), 404
    return jsonify(serialize(row))


@app.post("/resultados")
def create_result():
    try:
        product, revenue, rank = parse_result_payload(request.get_json(silent=True), include_rank=True)
        with get_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO resultados (product, total_revenue, rank) VALUES (%s, %s, %s) RETURNING product",
                (product, revenue, rank),
            )
            created_product = cursor.fetchone()[0]
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except psycopg2.IntegrityError:
        return jsonify(error="producto o posicion ya existentes"), 409
    return jsonify(product=created_product), 201


@app.put("/resultados/<path:product>")
def update_result(product):
    try:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            raise ValueError("se requiere un objeto JSON")
        values = [product]
        if "total_revenue" in payload:
            revenue = Decimal(str(payload["total_revenue"]))
            if not revenue.is_finite() or revenue < 0:
                raise ValueError
            values.append(revenue)
        else:
            values.append(None)
        if "rank" in payload:
            rank = int(payload["rank"])
            if rank < 1 or rank > 10:
                raise ValueError
            values.append(rank)
        else:
            values.append(None)
        if values[1] is None and values[2] is None:
            raise ValueError("indica total_revenue o rank")
    except (InvalidOperation, TypeError, ValueError):
        return jsonify(error="datos de actualizacion invalidos"), 400

    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "UPDATE resultados SET total_revenue = COALESCE(%s, total_revenue), rank = COALESCE(%s, rank) WHERE product = %s",
            (values[1], values[2], product),
        )
        if cursor.rowcount == 0:
            return jsonify(error="resultado no encontrado"), 404
    return jsonify(status="updated", product=product)


@app.delete("/resultados/<path:product>")
def delete_result(product):
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM resultados WHERE product = %s", (product,))
        if cursor.rowcount == 0:
            return jsonify(error="resultado no encontrado"), 404
    return jsonify(status="deleted", product=product)


@app.get("/ssh-check")
def ssh_check():
    try:
        result = subprocess.run(
            ["ssh", "pipeline@hadoop", "printf 'SSH API a Hadoop OK\\n'"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        detail = getattr(error, "stderr", "") or str(error)
        return jsonify(error="no se pudo conectar por SSH", detail=detail), 503
    return jsonify(output=result.stdout.strip())


def wait_for_database():
    for attempt in range(30):
        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "CREATE TABLE IF NOT EXISTS resultados ("
                        "product TEXT PRIMARY KEY, "
                        "total_revenue NUMERIC(18, 2) NOT NULL CHECK (total_revenue >= 0), "
                        "rank INTEGER NOT NULL UNIQUE CHECK (rank BETWEEN 1 AND 10))"
                    )
            return
        except psycopg2.OperationalError:
            if attempt == 29:
                raise
            time.sleep(2)


if __name__ == "__main__":
    wait_for_database()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))