"""Tests for core."""

import grafanalib.core as G


def test_table_styled_columns() -> None:
    t = G.Table.with_styled_columns(
        columns=[(G.Column("Foo", "foo"), G.ColumnStyle()), (G.Column("Bar", "bar"), None)],
        dataSource="some data source",
        targets=[G.Target(expr="some expr")],
        panel=G.Panel(title="table title"),
    )
    assert t.columns == [G.Column("Foo", "foo"), G.Column("Bar", "bar")]
    assert t.styles == [G.ColumnStyle(pattern="Foo")]


def test_single_stat() -> None:
    data_source = "dummy data source"
    targets = ["dummy_prom_query"]
    title = "dummy title"
    single_stat = G.SingleStat(dataSource=data_source, targets=targets, panel=G.Panel(title))
    data = single_stat.to_json_data()
    assert data["targets"] == targets
    assert data["datasource"] == data_source
    assert data["title"] == title
