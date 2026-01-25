## api/endpoints.md

# Phase-1 API Endpoints

| Endpoint          | Method | Description                                  | Port |
|------------------|--------|----------------------------------------------|------|
| /api/nodes        | GET    | List all nodes and metadata                  | 3033 |
| /api/node_health  | GET    | Latest health metrics                         | 3033 |
| /api/node_alerts  | GET    | Active alerts                                | 3033 |
| /api/node/:id     | GET    | Node detail metrics + alerts                 | 3033 |
| /api/fork_min_version | GET | Current network minimum version             | 3033 |


- Phase-1 API is read-only
- Pollers update health and alert tables internally

---
