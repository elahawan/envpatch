# envpatch

> Utility to diff and selectively merge `.env` files across environments with conflict resolution.

---

## Installation

```bash
pip install envpatch
```

Or with [pipx](https://pypa.github.io/pipx/):

```bash
pipx install envpatch
```

---

## Usage

### Diff two `.env` files

```bash
envpatch diff .env.development .env.production
```

### Selectively merge variables into a target file

```bash
envpatch merge .env.staging .env.production --output .env.production
```

During a merge, `envpatch` will prompt you to resolve any conflicting keys:

```
CONFLICT: DATABASE_URL
  [1] staging:    postgres://localhost/myapp_staging
  [2] production: postgres://prod-host/myapp
  Keep which? (1/2/skip):
```

### Patch a file with specific keys from a source

```bash
envpatch patch .env.local --keys API_KEY,DEBUG --from .env.example
```

### Options

| Flag | Description |
|------|-------------|
| `--output` | Write result to a file instead of stdout |
| `--dry-run` | Preview changes without writing |
| `--force` | Overwrite conflicts with source values |
| `--silent` | Skip prompts, keep target values on conflict |

---

## License

[MIT](LICENSE) © envpatch contributors