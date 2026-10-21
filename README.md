# Icon Manager

Assigns Windows folder icons from rules. You keep a library of `.ico` files,
each with a `.json` next to it describing which folders it belongs to, and
the tool walks your search folders and writes the matching `desktop.ini`.

Windows only: the icon is applied by writing `desktop.ini` and marking files
with `attrib`. Everything except those `attrib` calls runs anywhere, which is
what makes the test suite portable.

## Usage

```bash
python -m icon_manager --library --create   # create a config for every new icon
python -m icon_manager --library --update   # refresh configs from the template
python -m icon_manager --library --archive  # move icons without rules to __archive__
python -m icon_manager --library --delete   # delete the configs (icons stay)

python -m icon_manager --content --create     # apply icons to matching folders
python -m icon_manager --content --re-create  # restore desktop.ini lost to OneDrive
python -m icon_manager --content --delete     # remove what this tool wrote
```

`--library` works on the icon library, `--content` on the searched folders.
Short forms: `-l`, `-c`, `-a` (create), `-r` (re-create), `-u`, `-d`,
`-v` (archive).

## How a folder gets its icon

```
app_config.config ──> user config(s) ──> search folders
                                    └──> icon library

  crawler          walks each search folder into a Folder tree
     │
  filters          drops excluded / project folders and exclude-rule matches
     │
  rule matching    first IconSetting whose rules allow the folder wins
     │
  DesktopIniCreator  writes desktop.ini (+ copies the icon when configured)
```

A `desktop.ini` written here always contains `IconManager=1`. That marker is
the safety mechanism: the tool refuses to overwrite or delete a `desktop.ini`
without it, so files written by Windows or other programs are left alone.

## Configuration

Config files live in one folder, by default `%APPDATA%/Icon-Manager`, and are
created from templates in `icon_manager/resources/` on first run.

### `app_config.config`

```json
{
  "user_configs": "C:\\Users\\me\\AppData\\Roaming\\Icon-Manager",
  "before_or_after": ["_", "-"]
}
```

`before_or_after` are affixes a folder name may carry around a rule value, so
a rule for `docs` can also match `_docs` or `docs-`. A rule opts in with
`"before_or_after": true`.

### A user config, e.g. `me.config`

```json
{
  "config": {
    "icons_path": "%OneDriveConsumer%\\Bilder\\Icons",
    "search_folders": [{ "path": "C:\\workspace", "copy_icon": true }],
    "code_folders": [".git", ".venv"],
    "exclude_folders": ["__pycache__", "obj"],
    "before_or_after": [],
    "copy_icon": true
  }
}
```

- `icons_path` – the icon library
- `search_folders` – where to apply icons; `copy_icon` overrides the global one
- `code_folders` – folder names marking a project, not searched further
- `exclude_folders` – folder names never searched
- `copy_icon` – copy the icon into a hidden `__icon__` folder next to
  `desktop.ini` instead of referencing the library. A copied icon is
  referenced relative to the folder, so it survives the folder being moved.

Paths may use `%VARIABLE%`; unset variables are left as-is.

### An icon config, e.g. `docs.json` beside `docs.ico`

```json
{
  "config": {
    "order": 5,
    "name": { "operator": "any", "rules": [{ "equals": ["docs", "documentation"] }] }
  }
}
```

A section per folder attribute — `name`, `path`, `parent_name`, `parent_path` —
each with a list of rules. `order` is the tie breaker when several icons match
(lower wins). `copy_icon` here overrides both the search folder and the user
config.

#### Rules

| Rule | Matches when the attribute |
| --- | --- |
| `equals` / `not_equals` | is (not) one of the values |
| `starts_with` / `ends_with` / `start_or_ends_with` | begins/ends with a value |
| `contains` / `not_contains` | (does not) contain a value |
| `contains_file` / `not_contains_file` | folder (does not) hold a file with that extension |
| `contains_folder` / `not_contains_folder` | folder (does not) hold a subfolder with that name |
| `chained` | a nested list of rules, combined by `operator` |

Per-rule options: `operator` (`any`/`all`), `case_sensitive` (default false),
`before_or_after` plus optional `before_or_after_values`, and `level` for the
`contains_file`/`contains_folder` search depth (default 1).

`operator` appears at three levels and always means the same thing: `any`
requires one child to match, `all` requires every child. On a rule it applies
to the rule's values, on an attribute section to its rules, and on the config
to its sections.

### `excluded_rules.config`

The same rule sections, but a list of them, and a folder matching any of them
is skipped together with everything below it.

## Architecture

```
icon_manager/
  __main__.py        CLI: parse options, dispatch to the service
  services/          ConfigService (one user config), IconsAppService (fan-out)
  config/            reading app_config and the user configs
  library/           the icon library: icons paired with their rules
  crawler/           walking folders into a Folder tree, and filtering it
  rules/             the rule engine; factory/ builds it from config dicts
  content/           what lands on disk: desktop.ini, __icon__, icon files
  interfaces/        the shared abstractions (paths, actions, builders)
  data/              reading and writing JSON and INI files
```

Two ideas carry most of the design:

**One matcher abstraction.** `rules.base.FolderMatcher` has `is_allowed`,
`is_empty`, `clean_empty` and `setup_rules`. A single rule, a group of rules
for one attribute, an icon config's rule set and the exclude manager all
satisfy it, so composing them is a plain Composite and a caller only ever
needs `is_allowed`.

**Two path representations, on purpose.** `Node`/`File`/`Folder` are
dataclasses holding a crawl result — cheap, with a parent link, and the rules
match against them. `PathModel`/`FileModel`/`FolderModel` wrap a single path
with the operations that touch the disk. The crawler produces the first, the
content controllers act through the second.

Per-configuration state stays per configuration: builders are constructed in
`__init__` rather than as default arguments, and the excluded/project folder
names travel in `FilterOptions`. Both were shared before, which made one
user config's rules apply to another.

## Development

```bash
uv sync --all-groups
uv run pytest                      # 176 tests
uv run pytest --cov=icon_manager   # ~89% coverage
uv run ruff check icon_manager tests
uv run ruff format icon_manager tests
uv run pyright
```

The tests drive the real code against a real directory tree under `tmp_path`;
`tests/conftest.py` has the helpers for building a library and a folder tree.
Prefer adding to a `*_behaviour.py` file over asserting on internal calls —
the previous suite verified collaborators with mocks and stayed green while
the tool did not apply a single icon.
