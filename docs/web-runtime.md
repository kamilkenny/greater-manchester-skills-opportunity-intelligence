# GM SkillsFlow Web Runtime

The public Plotly Dash application uses a deliberately lean runtime.

`requirements-web.txt` is the Azure App Service deployment dependency
manifest.

The web application does not require the analytics-engineering packages
used by ingestion and transformation workloads, including pandas and
NumPy.

Application code imports `gm_skills` directly from the repository `src`
directory through the deployment startup configuration.

Runtime principles:

- one Gunicorn worker on the free deployment tier;
- one active in-memory validated snapshot;
- no pandas DataFrame cache;
- no local snapshot history;
- Azure Blob contains only slot-a, slot-b and manifest.json;
- manifest checks do not reload data when snapshot_id is unchanged;
- failed refreshes retain the last-known-good in-memory snapshot.
