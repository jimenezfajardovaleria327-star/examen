#!/usr/bin/env python3
import argparse
import csv
from decimal import Decimal, InvalidOperation


def calculate(input_path):
    totals = {}
    with open(input_path, newline="", encoding="utf-8") as source:
        for raw_line in source:
            try:
                fields = next(csv.reader([raw_line]))
            except (csv.Error, StopIteration):
                continue
            if not fields or fields[0].strip().lower() == "id" or len(fields) != 8:
                continue
            product = fields[4].strip()
            try:
                quantity = int(fields[5])
                unit_price = Decimal(fields[6])
                if not product or quantity < 0 or not unit_price.is_finite():
                    continue
            except (ValueError, InvalidOperation):
                continue
            totals[product] = totals.get(product, Decimal("0")) + quantity * unit_price

    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))[:10]
    return [(product, f"{revenue:.2f}", rank) for rank, (product, revenue) in enumerate(ranked, start=1)]


def main():
    parser = argparse.ArgumentParser(description="Top 10 productos por ingreso anual")
    parser.add_argument("input", help="Ruta del CSV de ventas")
    parser.add_argument("output", help="Archivo TSV de salida")
    args = parser.parse_args()

    with open(args.output, "w", encoding="utf-8", newline="") as destination:
        for product, revenue, rank in calculate(args.input):
            destination.write(f"{product}\t{revenue}\t{rank}\n")


if __name__ == "__main__":
    main()