Decayer
=======

Decayer is a simple Python script that can decay files in a rclone remote path by frequency and age.

It is usefull to manage things like backups that are create periodically and you want to keep recent ones at a higher frequency and older ones at a lower frequency.

For example:

```
decayer remote:/path/to/backups 1d@2d 7d5h@7d 0@30d
```

Will keep:
- all files younger than 2 days
- 1 file per day for files older than 2 days and younger than 1 week
- 1 file per week and 5 hours for files older than 1 week and younger than 30 days
- no files older than 30 days

## Installation

Can be done with `pipx`:

```
pipx install git+https://github.com/p2004a/decayer.git
```

Or by just copying the `decayer.py` file to a directory in your PATH as it is a standalone script.

## Development

Setup:

```
python3 -m venv .venv
source .venv/bin/activate  # but I also recommend https://direnv.net/ that will load .envrc automatically
pip install -e '.[dev]'
pre-commit install
```

Run all lints and tests with
```
pre-commit run --all-files
```
but it will be run automatically before every commit.
