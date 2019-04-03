"""Tests for OpenTSDB datasource"""

from io import StringIO

import grafanalib.core as G
from grafanalib import _gen
from grafanalib.opentsdb import OpenTSDBFilter, OpenTSDBTarget


def test_serialization_opentsdb_target():
    """Serializing a graph doesn't explode."""
    graph = G.Graph(
        title="CPU Usage",
        dataSource="OpenTSDB data source",
        targets=[
            OpenTSDBTarget(
                metric="cpu",
                alias="$tag_instance",
                filters=[OpenTSDBFilter(value="*", tag="instance", type="wildcard", groupBy=True)],
            )
        ],
        id=1,
        yAxes=G.YAxes(
            left=G.YAxis(format=G.SHORT_FORMAT, label="CPU seconds / second"),
            right=G.YAxis(format=G.SHORT_FORMAT),
        ),
    )
    stream = StringIO()
    _gen.write_dashboard(graph, stream)
    assert stream.getvalue() != ""
