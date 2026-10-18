#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from health_db import list_runs, save_run


def import_csv(args: argparse.Namespace) -> int:
    if not args.confirm:
        raise SystemExit("Refusing import without --confirm")
    with args.source.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise SystemExit("No health runs found")
    for row in rows:
        save_run(row)
        print(f"{row['date']} {row['start_time']} {row['distance_km']} km")
    return 0


def list_command(_: argparse.Namespace) -> int:
    for row in list_runs():
        print(f"{row['date']} {row['start_time']} {row['distance_km']} km {row['duration']}")
    return 0


def upsert_json(args: argparse.Namespace) -> int:
    row = json.loads(args.source.read_text(encoding="utf-8")) if args.source else json.load(__import__("sys").stdin)
    required = {"date", "start_time", "distance_km", "duration"}
    missing = sorted(required - set(row))
    if missing:
        raise SystemExit("Missing required fields: " + ", ".join(missing))
    save_run(row)
    print(f"saved {row['date']} {row['start_time']}")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Stanley Health database manager")
    commands = result.add_subparsers(dest="command", required=True)
    importer = commands.add_parser("import-csv")
    importer.add_argument("--source", type=Path, required=True)
    importer.add_argument("--confirm", action="store_true")
    importer.set_defaults(handler=import_csv)
    listing = commands.add_parser("list")
    listing.set_defaults(handler=list_command)
    upsert = commands.add_parser("upsert-json")
    upsert.add_argument("--source", type=Path)
    upsert.set_defaults(handler=upsert_json)
    return result


if __name__ == "__main__":
    args = parser().parse_args()
    raise SystemExit(args.handler(args))
