# Migration Guide: v0.2 to Morpheus Lite Laboratory v1.0

## Overview

Laboratory v1.0 freezes the validated v0.2 implementation as a stable teaching and research baseline. The architecture remains compatible, while the dashboard and documentation are updated for a consistent student workflow.

## Main changes

- Product name updated to **Morpheus Lite Laboratory v1.0**.
- Dashboard uses `alert_id` as the single shared selection key.
- All Cases, Human Decision Queue, and Case Details are synchronized.
- The first-column **Select** checkbox is the supported selection mechanism.
- Human decisions and justifications remain linked to `alert_id` and `correlation_id`.
- Student, instructor, research-data, release, architecture, and troubleshooting guides are included.
- Version freeze and change-control policy are documented.

## Upgrade steps

1. Back up the existing directory.
2. Replace `dashboard.py` with the v1.0 synchronized dashboard.
3. Replace or merge the updated Markdown documentation.
4. Keep local `.env`, API keys, model files, audit logs, and exports outside the replacement operation.
5. Confirm topic mappings in `config/topics.yaml`.
6. Run:

```bash
pip install -e ".[research,dev]"
pytest -q
```

7. Validate one complete workflow from telemetry to human decision and export.

## Compatibility

The root-level startup commands remain unchanged. Existing v0.2 topic names and core record fields are preserved.
