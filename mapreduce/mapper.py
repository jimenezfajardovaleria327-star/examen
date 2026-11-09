#!/usr/bin/env python3
import csv
import sys
from decimal import Decimal, InvalidOperation


def main():
    for raw_line in sys.stdin:
        try:
            fields = next(csv.reader([raw_line]))
        except (csv.Error, StopIteration):
            continue
        if not fields or fields[0].strip().lower() == "id":
            continue
        if len(fields) != 8:
            continue

        product = fields[4].strip()
        if not product:
            continue
        try:
            quantity = int(fields[5])
            unit_price = Decimal(fields[6])
            if quantity < 0 or not unit_price.is_finite():
                continue
            revenue = unit_price * quantity
        except (ValueError, InvalidOperation):
            continue

        print(f"{product}\t{revenue:.2f}")


if __name__ == "__main__":
    main()