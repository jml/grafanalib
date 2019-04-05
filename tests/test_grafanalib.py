"""Tests for Grafanalib."""

from io import StringIO

import grafanalib.core as G
from grafanalib import _gen

# TODO: Use Hypothesis to generate a more thorough battery of smoke tests.


def test_serialization() -> None:
    """Serializing a graph doesn't explode."""
    graph = G.Graph(
        panel=G.Panel(title="CPU Usage by Namespace (rate[5m])"),
        dataSource="My data source",
        targets=[
            # G.Target(
            #     expr="namespace:container_cpu_usage_seconds_total:sum_rate",
            #     legendFormat="{{namespace}}",
            #     refId="A",
            # )
        ],
        yAxes=G.YAxes(
            left=G.YAxis(format=G.NumberFormat.SHORT, label="CPU seconds / second"),
            right=G.YAxis(format=G.NumberFormat.SHORT),
        ),
    )
    stream = StringIO()
    _gen.write_dashboard(graph, stream)
    assert stream.getvalue() != ""


def test_auto_id() -> None:
    """auto_panel_ids() provides IDs for all panels without IDs already set."""
    dashboard = G.Dashboard(
        title="Test dashboard",
        rows=[
            G.Row(
                panels=[
                    G.Graph(
                        G.Panel(title="CPU Usage by Namespace (rate[5m])"),
                        dataSource="My data source",
                        targets=[
                            G.Target(expr="whatever", legendFormat="{{namespace}}", refId="A")
                        ],
                        yAxes=G.YAxes(
                            left=G.YAxis(format=G.NumberFormat.SHORT, label="CPU seconds"),
                            right=G.YAxis(format=G.NumberFormat.SHORT),
                        ),
                    )
                ]
            )
        ],
    ).auto_panel_ids()
    assert dashboard.rows[0].panels[0].panel.id == 1


def test_row_show_title() -> None:
    row = G.Row().to_json_data()
    assert row["title"] == "New row"
    assert not row["showTitle"]

    row = G.Row(title="My title").to_json_data()
    assert row["title"] == "My title"
    assert row["showTitle"]

    row = G.Row(title="My title", showTitle=False).to_json_data()
    assert row["title"] == "My title"
    assert not row["showTitle"]
