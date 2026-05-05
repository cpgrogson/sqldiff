# sqldiff

Lightweight utility to diff schema changes between two database snapshots.

---

## Installation

```bash
pip install sqldiff
```

Or install from source:

```bash
git clone https://github.com/yourname/sqldiff.git && cd sqldiff && pip install .
```

---

## Usage

Compare two database snapshots and print the schema diff:

```bash
sqldiff snapshot_v1.sql snapshot_v2.sql
```

Use it as a Python library:

```python
from sqldiff import diff_schemas

changes = diff_schemas("snapshot_v1.sql", "snapshot_v2.sql")
for change in changes:
    print(change)
```

Example output:

```
[+] TABLE users
    [+] COLUMN email VARCHAR(255) NOT NULL
[-] TABLE legacy_sessions
[~] TABLE orders
    [~] COLUMN status: VARCHAR(50) -> VARCHAR(100)
```

### Options

| Flag | Description |
|------|-------------|
| `--format json` | Output diff as JSON |
| `--ignore-views` | Skip view definitions |
| `--summary` | Print a short summary only |

---

## Requirements

- Python 3.8+
- No external dependencies

---

## License

This project is licensed under the [MIT License](LICENSE).