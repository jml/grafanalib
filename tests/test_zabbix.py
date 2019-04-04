"""Tests for Zabbix Datasource"""

from io import StringIO

import grafanalib.core as G
import grafanalib.zabbix as Z
from grafanalib import _gen


def test_serialization_zabbix_target():
    """Serializing a graph doesn't explode."""
    graph = G.Graph(
        panel=G.Panel(title="CPU Usage"),
        dataSource="Zabbix data source",
        targets=[
            Z.zabbixMetricTarget(
                group="Zabbix Group",
                host="Zabbix Host",
                application="CPU",
                item="/CPU (load)/",
                functions=[Z.ZabbixSetAliasFunction("View alias")],
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


def test_serialization_zabbix_trigger_panel():
    """Serializing a graph doesn't explode."""
    graph = Z.ZabbixTriggersPanel(
        id=1,
        title="Zabbix Triggers",
        dataSource="Zabbix data source",
        triggers=Z.ZabbixTrigger(
            group="Zabbix Group", application="", trigger="/trigger.regexp/", host="/zabbix.host/"
        ),
    )
    stream = StringIO()
    _gen.write_dashboard(graph, stream)
    assert stream.getvalue() != ""
