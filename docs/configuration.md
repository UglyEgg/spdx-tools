# Configuration

`spdx-headers` looks for optional configuration in two places within the repository you pass via `--path` (or the current working directory by default):

1. A `[tool.spdx-headers]` section in `pyproject.toml`.
2. A `.spdx-headers.ini` file.

Both inputs are merged, with `_version.py` excluded by default.

## Using `pyproject.toml`

Add a table under `[tool.spdx-headers]`:

```toml
[tool.spdx-headers]
exclude = ["_version.py", "docs/conf.py"]
```

- `exclude` accepts a list of filenames (not glob patterns).
- This approach keeps configuration near other tooling settings and avoids extra files at the repo root.

## Using `.spdx-headers.ini`

Alternatively, place a `.spdx-headers.ini` alongside your source:

```ini
[spdx-headers]
exclude = _version.py docs/conf.py
```

- Entries are whitespace-separated filenames.
- You can use both `pyproject.toml` and the `.ini`; the union of exclusions applies.

## Recommendations

- Track configuration in version control so CI and contributors share the same exclusions.
- Keep the list minimal—only generated or vendored files that cannot maintain headers should be excluded.
- When distributing wheels or sdists, ship a sample configuration if consumers need specific exclusions.
