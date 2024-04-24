#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 Marek Rusinowski
# SPDX-License-Identifier: Apache-2.0 OR MIT

import argparse
import json
import re
import subprocess
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Generic, NamedTuple, Protocol, TypeVar

T = TypeVar("T")

TIMEDELTA_RE = re.compile(
    r"(((?P<days>\d+)d)?((?P<hours>\d+)h)?((?P<minutes>\d+)m)?((?P<seconds>\d+)s)?)|0"
)


def parse_timedelta(t: str) -> timedelta:
    """Parses a string into a timedelta."""
    match = TIMEDELTA_RE.fullmatch(t)
    if not match:
        msg = "Invalid timedelta: {t}"
        raise ValueError(msg)
    return timedelta(
        days=int(match["days"] or 0),
        hours=int(match["hours"] or 0),
        minutes=int(match["minutes"] or 0),
        seconds=int(match["seconds"] or 0),
    )


class DecayOpt(NamedTuple, Generic[T]):
    after: T
    period: T

    @staticmethod
    def from_str(s: str) -> "DecayOpt[timedelta]":
        period, after = s.split("@")
        return DecayOpt(parse_timedelta(after), parse_timedelta(period))


class Entry(NamedTuple, Generic[T]):
    time: T
    name: str


class FS(Protocol):
    def listdir(self, path: str) -> Iterable[Entry[datetime]]: ...
    def delete(self, path: str) -> None: ...


class RCloneFS:
    def listdir(self, path: str) -> Iterable[Entry[datetime]]:
        output = subprocess.check_output(
            ["rclone", "lsjson", "--no-mimetype", path], text=True
        )
        files = json.loads(output)
        return [
            Entry(datetime.fromisoformat(line["ModTime"]), line["Name"])
            for line in files
        ]

    def delete(self, path: str) -> None:
        subprocess.check_call(["rclone", "delete", path])


def decay(
    decays: Iterable[DecayOpt[float]], files: Iterable[Entry[float]]
) -> Iterable[str]:
    """Compute files to delete based on decay options.

    Args:
        decays: List of decay options: after what time to keep only one file per period
        files: List of files: name and how long ago they were modified

    Returns:
        List of files to delete
    """
    inf = float("inf")
    decays = sorted(decays)
    if not decays or decays[0].after != 0:
        decays = [DecayOpt(0.0, -inf), *decays]
    files = [Entry(-inf, ""), *sorted(files)]
    delete = []

    di = len(decays) - 1
    last = inf
    for i in range(len(files) - 1, 0, -1):
        while decays[di].after > files[i].time:
            di -= 1
        if decays[di].period == 0 or last - files[i - 1].time <= decays[di].period:
            delete.append(files[i].name)
        else:
            last = files[i].time

    return delete


def decay_files(
    fs: FS,
    now: datetime,
    path: str,
    decays: Iterable[DecayOpt[timedelta]],
    dry_run: bool = False,
) -> None:
    files = fs.listdir(path)

    fdecays = [
        DecayOpt(d.after.total_seconds(), d.period.total_seconds()) for d in decays
    ]
    ffiles = [Entry((now - f.time).total_seconds(), f.name) for f in files]

    to_delete = decay(fdecays, ffiles)
    for f in to_delete:
        if not dry_run:
            fs.delete(f"{path}/{f}")
        print(f"Deleted {f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Decay versions of files")
    parser.add_argument("path", help="Path to the directory to decay")
    parser.add_argument(
        "decays",
        nargs="+",
        type=DecayOpt.from_str,
        help="Decay options in the form 'period@after', e.g. '1d2h@7d', '0@30d'",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not delete files")
    args = parser.parse_args()
    decay_files(RCloneFS(), datetime.now(tz=UTC), args.path, args.decays, args.dry_run)


if __name__ == "__main__":
    main()
