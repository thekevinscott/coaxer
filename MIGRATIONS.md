# Migrations

This file is the source of truth for downstream-consumer upgrade instructions
when coaxer ships a breaking change or a notable behavior-only change. See
[CHANGELOG.md](CHANGELOG.md) for the full history of every release — this
file only covers the subset that requires consumer action.

Each entry is scoped to the release that introduced the change and follows a
5-section template:

```markdown
## <version> — <short slug>

### (a) Summary
One paragraph: what broke, why the change was made, who is affected.

### (b) Required changes
| Area | Before | After |
| ---- | ------ | ----- |

### (c) Deprecations removed
(list or "None.")

### (d) Behavior changes without code changes
(list or "None.")

### (e) Verification
Exact command + expected output (or the error a consumer will see if they
skipped a step).
```

---

## Unreleased — sibling-file resolution no longer implies file on slash

### (a) Summary
`_resolve_value` previously raised `FileNotFoundError` for any input whose value contained `/` (or ended in `.md` / `.txt` / `.json` / `.png` / `.jpg` / `.pdf`), assuming it was a sibling-file path. That broke legitimate scalar inputs — GitHub `owner/name`, dates formatted `YYYY/MM/DD`, URLs as strings, etc. Resolution is now driven by `_schema.json`: a field is treated as file-backed when it declares `"type": "file"` or `"backing": "file"`, falling back to implicit resolution only when the value is a plain filename that exists on disk. Affected: any label folder whose schema has scalar inputs that may legitimately contain `/`.

### (b) Required changes

| Area | Before | After |
| ---- | ------ | ----- |
| Scalar input with `/` | Stored in a sibling `.txt` file because `"x": "foo/bar"` raised | `"x": "foo/bar"` works as-is |
| Explicit file-backed input | `"x": "x.md"` (relied on extension heuristic) | Either keep the existing form (still works when `x.md` exists on disk) **or** add `"backing": "file"` (or `"type": "file"`) to the field's `_schema.json` entry to opt in unambiguously |

Example schema with the new opt-in:

```json
{
  "inputs": {
    "readme": {"type": "str", "backing": "file"},
    "repo_name": {"type": "str"}
  },
  "output": {"type": "enum", "values": ["true", "false"]}
}
```

### (c) Deprecations removed
None — this is a behavior fix, not a deprecation removal.

### (d) Behavior changes without code changes
- **`/` in a scalar input value is no longer treated as a path indicator.** Previously raised `FileNotFoundError`; now passes through as a string. If you were relying on the error to catch typos in file paths, mark the field with `"backing": "file"` (or `"type": "file"`) in `_schema.json` to keep that strictness.
- **Extension-based file detection is gone.** Values ending in `.md` / `.txt` / `.json` / `.png` / `.jpg` / `.pdf` are no longer auto-treated as file paths unless the named file actually exists on disk in the record directory or the schema marks the field as file-backed.

### (e) Verification
For a label folder where an input genuinely holds slashes:

```bash
coax labels/my-task --out prompts/my-task --optimizer none
```

Should compile cleanly. Before the fix this would print:

```
FileNotFoundError: Sibling file not found: labels/my-task/0001/expo/skills
```

For a schema-declared file field where the file is missing, you should still see a `FileNotFoundError` mentioning the expected path — the strict mode is now opt-in via schema rather than guessed from the value.

---

## 0.3.x — public API replaced

### (a) Summary
Coaxer's public API was rebuilt around a label-folder / compiled-prompt split.
DSPy is no longer part of the exported surface, the CLI binary was renamed
from `coaxer` to `coax`, and the `CoaxPrompt` class was renamed to
`CoaxedPrompt`. The interactive labeling TUI and the `/optimize` skill
installer were removed. Anyone using the 0.2.x public API must update imports,
CLI invocations, and workflow scripts.

### (b) Required changes
| Area            | Before                                   | After                                                |
| --------------- | ---------------------------------------- | ---------------------------------------------------- |
| CLI binary      | `coaxer distill <labels> --out <prompts>` | `coax <labels> --out <prompts>`                      |
| Prompt class    | `from coaxer import CoaxPrompt`           | `from coaxer import CoaxedPrompt`                    |
| Loading a prompt | `coaxer.load_predict("prompts/<name>")`   | `CoaxedPrompt("prompts/<name>")`                     |
| Labeling TUI    | `coaxer label`                            | Removed — edit the label folder directly, or have an agent populate `record.json` + sibling files. |
| Skill installer | `coaxer install`                          | Removed — the `/optimize` skill's workflow is now just `coax`. |

### (c) Deprecations removed
- `coaxer.load_predict` (undocumented path re-export of DSPy's `Predict`).
- `coaxer label` CLI and the `coaxer/tui/` package.
- `coaxer install` CLI and the `coaxer/skills/` package.
- The `coaxer` console script (replaced by `coax`).

### (d) Behavior changes without code changes
- Prompt templating switched from Python-style `{field}` to Jinja2 `{{ field }}`
  to avoid collisions with JSON and code blocks inside labels. Existing prompt
  artifacts compiled with 0.2.x must be rebuilt with `coax`.
- The default optimizer is now `--optimizer none` (schema-derived template, no
  network access). Pass `--optimizer gepa` to opt into DSPy 3 + GEPA
  optimization.

### (e) Verification
```bash
coax --help
```
Should print the new CLI's usage (`coax <labels> --out <prompts> [--optimizer ...]`).

```bash
python -c "from coaxer import CoaxedPrompt; print(CoaxedPrompt.__module__)"
```
Should print `coaxer.prompt` and exit 0. If you see
`ImportError: cannot import name 'CoaxPrompt'` or
`command not found: coaxer`, you're still on 0.2.x.

---

## 0.2.x — package renamed `karat` → `coaxer` and karat shim removed

### (a) Summary
The library was renamed from `karat` to `coaxer` and moved to
`https://github.com/thekevinscott/coaxer`. The `karat` distribution was kept
as a thin re-export shim that emitted a `DeprecationWarning`, then removed
in a later 0.2.x release. Anyone still depending on `karat` must switch the
distribution name and every import.

### (b) Required changes
| Area    | Before                  | After                    |
| ------- | ----------------------- | ------------------------ |
| Install | `uv add karat`          | `uv add coaxer`          |
| Import  | `from karat import X`   | `from coaxer import X`   |
| Repo    | `github.com/.../karat`  | `github.com/thekevinscott/coaxer` |

### (c) Deprecations removed
- The `karat` shim package (`from karat import X` used to re-export from
  `coaxer` with a `DeprecationWarning`). The shim is gone; `karat` on PyPI is
  no longer published.

### (d) Behavior changes without code changes
None.

### (e) Verification
```bash
python -c "from karat import CoaxedPrompt"
```
Should raise `ModuleNotFoundError: No module named 'karat'`. If the import
succeeds, you still have the old shim pinned — check your lockfile for a
`karat` entry and replace it with `coaxer`.

```bash
python -c "from coaxer import CoaxedPrompt; print('ok')"
```
Should print `ok`.
