"""Tests for OpenTSDB datasource"""

from io import StringIO

import grafanalib.core as G
from grafanalib import _gen
from grafanalib.opentsdb import OpenTSDBFilter, OpenTSDBTarget, QueryFilter


def test_serialization_opentsdb_target() -> None:
    """Serializing a graph doesn't explode."""
    graph = G.Graph(
        panel=G.Panel(title="CPU Usage"),
        dataSource="OpenTSDB data source",
        targets=[
            OpenTSDBTarget(
                metric="cpu",
                alias="$tag_instance",
                filters=[
                    OpenTSDBFilter(
                        value="*", tag="instance", type=QueryFilter.WILDCARD, groupBy=True
                    )
                ],
            )
        ],
        yAxes=G.YAxes(
            left=G.YAxis(format=G.NumberFormat.SHORT, label="CPU seconds / second"),
            right=G.YAxis(format=G.NumberFormat.SHORT),
        ),
    )
    stream = StringIO()
    _gen.write_dashboard(graph, stream)
    assert stream.getvalue() != ""
