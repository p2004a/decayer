import unittest
from collections.abc import Iterable
from datetime import datetime, timedelta

from decayer import DecayOpt, Entry, decay, decay_files, parse_timedelta


class TestingFS:
    deleted: set[str]

    def __init__(self, files: Iterable[Entry[datetime]]) -> None:
        self.files = list(files)
        self.deleted = set()

    def listdir(self, path: str) -> Iterable[Entry[datetime]]:
        return self.files

    def delete(self, path: str) -> None:
        self.deleted.add(path)


class TestDecay(unittest.TestCase):

    def test_timedelta_parsing(self) -> None:
        self.assertEqual(
            parse_timedelta("1d2h3m4s"),
            timedelta(days=1, hours=2, minutes=3, seconds=4),
        )
        self.assertEqual(parse_timedelta("1d"), timedelta(days=1))
        self.assertEqual(parse_timedelta("0"), timedelta())

    def test_parse_decay_opt(self) -> None:
        self.assertEqual(
            DecayOpt.from_str("1d2h@7d"),
            DecayOpt(timedelta(days=7, hours=0), timedelta(days=1, hours=2)),
        )
        self.assertEqual(
            DecayOpt.from_str("0@30d"), DecayOpt(timedelta(days=30), timedelta())
        )

    def test_decay(self) -> None:
        decays = [DecayOpt(after=10.0, period=3.0), DecayOpt(after=20.0, period=0.0)]
        files = [
            Entry(1.0, "a"),
            Entry(2.0, "b"),
            Entry(3.0, "c"),
            Entry(10.0, "d"),
            Entry(11.0, "e"),
            Entry(13.0, "f"),
            Entry(14.0, "g"),
            Entry(15.0, "h"),
            Entry(20.0, "i"),
            Entry(22.0, "j"),
        ]
        self.assertEqual(set(decay(decays, files)), {"e", "g", "i", "j"})
        self.assertEqual(decay([], []), [])

    def test_decay_files(self) -> None:
        files = [
            Entry(datetime.fromisoformat("2021-01-01T00:00:00"), "a"),
            Entry(datetime.fromisoformat("2021-01-02T00:00:00"), "b"),
            Entry(datetime.fromisoformat("2021-01-03T00:00:00"), "c"),
            Entry(datetime.fromisoformat("2021-01-04T00:00:00"), "d"),
            Entry(datetime.fromisoformat("2021-01-05T00:00:00"), "e"),
            Entry(datetime.fromisoformat("2021-01-06T00:00:00"), "f"),
        ]
        fs = TestingFS(files)
        decay_files(
            fs,
            datetime.fromisoformat("2021-01-07T03:00:01"),
            "path",
            [DecayOpt.from_str("2d@4d")],
        )
        self.assertEqual(fs.deleted, {"path/b"})
