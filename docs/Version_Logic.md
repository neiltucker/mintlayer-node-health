## docs/Version_Logic.md

# Version Comparison Logic

## Canonical Version Parsing
- Strip `v` prefix
- Parse semantic version components
- Ignore build metadata
- Treat pre-releases conservatively

## Comparison Rules
| Node Version | Required Version | Result |
|-------------|----------------|--------|
| 1.2.0 | 1.2.0 | ✅ Compatible |
| 1.2.1 | 1.2.0 | ✅ Compatible |
| 1.2.0-rc1 | 1.2.0 | ⚪ Unknown |
| 1.3.0-dev | 1.2.0 | ⚪ Unknown |

- `fork_compatibility_status` = Compatible / Outdated / Unknown
- Cache version per node 5–10 min, refresh on restart or version change

---

