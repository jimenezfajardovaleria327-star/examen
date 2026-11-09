#!/usr/bin/env python3
import sys
from decimal import Decimal, InvalidOperation


def main():
    totals = {}
    for line in sys.stdin:
        fields = line.rstrip("\n").split("\t")
        if len(fields) != 2:
            continue
        product = fields[0]
        try:
            revenue = Decimal(fields[1])
            if not revenue.is_finite():
                continue
        except InvalidOperation:
            continue
        totals[product] = totals.get(product, Decimal("0")) + revenue

    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))[:10]
    for rank, (product, revenue) in enumerate(ranked, start=1):
        print(f"{product}\t{revenue:.2f}\t{rank}")


if __name__ == "__main__":
    main()