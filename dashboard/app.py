from pathlib import Path

from dash import Dash, Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate
from flask import jsonify

from dashboard.pages import borough, mbacc, methodology, overview, trends
from gm_skills.serving.snapshot_store import SnapshotStore

ROOT = Path(__file__).resolve().parent


store = SnapshotStore.from_environment()
store.refresh()


def compact_status():
    status = store.status()

    return {
        "snapshot_id": status.get("snapshot_id"),
        "serving_status": status.get("serving_status"),
        "active_slot": status.get("active_slot"),
        "published_at_utc": status.get("published_at_utc"),
        "has_error": bool(status.get("last_error")),
    }


app = Dash(
    __name__,
    assets_folder=str(ROOT / "assets"),
    suppress_callback_exceptions=True,
    title="GM SkillsFlow",
    update_title=None,
)

server = app.server


app.layout = html.Div(
    [
        dcc.Location(
            id="url",
            refresh=False,
        ),
        dcc.Store(
            id="snapshot-version",
            data=compact_status(),
        ),
        dcc.Interval(
            id="snapshot-refresh",
            interval=5 * 60 * 1000,
            n_intervals=0,
        ),
        html.Div(
            id="page-content",
        ),
    ]
)


@server.route("/healthz")
def health():
    status = store.status()

    response_code = (
        200
        if status.get("snapshot_id")
        else 503
    )

    return (
        jsonify(
            {
                "service": "gm-skillsflow",
                "status": status.get(
                    "serving_status"
                ),
                "snapshot_id": status.get(
                    "snapshot_id"
                ),
                "active_slot": status.get(
                    "active_slot"
                ),
            }
        ),
        response_code,
    )


@app.callback(
    Output(
        "snapshot-version",
        "data",
    ),
    Input(
        "snapshot-refresh",
        "n_intervals",
    ),
    State(
        "snapshot-version",
        "data",
    ),
    prevent_initial_call=True,
)
def refresh_snapshot(
    _n_intervals,
    previous,
):
    store.refresh()

    current = compact_status()

    if current == previous:
        raise PreventUpdate

    return current


@app.callback(
    Output(
        "page-content",
        "children",
    ),
    Input(
        "url",
        "pathname",
    ),
    Input(
        "snapshot-version",
        "data",
    ),
)
def route_page(
    pathname,
    _snapshot_version,
):
    page_name = app.strip_relative_path(
        pathname
    )

    if not page_name:
        return overview.layout(
            store
        )

    if page_name == "borough":
        return borough.layout(
            store
        )

    if page_name == "mbacc":
        return mbacc.layout(
            store
        )

    if page_name == "trends":
        return trends.layout(
            store
        )

    if page_name == "methodology":
        return methodology.layout(
            store
        )

    return html.Div(
        className="content",
        children=[
            html.H1(
                "Page not found"
            ),
            dcc.Link(
                "Return to Overview",
                href="/",
            ),
        ],
    )


overview.register_callbacks(
    app,
    store,
)

borough.register_callbacks(
    app,
    store,
)

mbacc.register_callbacks(
    app,
    store,
)

trends.register_callbacks(
    app,
    store,
)



@server.route("/refresh-data", methods=["POST"])
def refresh_data():
    """Reload the latest validated published snapshot."""

    before_status = store.status()
    before_snapshot = before_status.get(
        "snapshot_id"
    )

    try:
        store.refresh()

        status = store.status()

        after_snapshot = status.get(
            "snapshot_id"
        )

        changed = bool(
            after_snapshot
            and after_snapshot != before_snapshot
        )

        return jsonify(
            {
                "ok": True,
                "changed": changed,
                "snapshot_id": after_snapshot,
                "published_at_utc": status.get(
                    "published_at_utc"
                ),
                "serving_status": status.get(
                    "serving_status"
                ),
                "last_successful_refresh_at":
                    status.get(
                        "last_successful_refresh_at"
                    ),
                "message": (
                    "Updated to latest published snapshot."
                    if changed
                    else
                    "Already showing latest published snapshot."
                ),
            }
        )

    except Exception as exc:
        status = store.status()

        return (
            jsonify(
                {
                    "ok": False,
                    "changed": False,
                    "snapshot_id": status.get(
                        "snapshot_id"
                    ),
                    "message": (
                        "Refresh failed. The current "
                        "validated snapshot remains active."
                    ),
                    "detail": str(exc),
                }
            ),
            503,
        )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8050,
        debug=False,
    )
