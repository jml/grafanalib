"""
This is an exemplary Grafana board that uses an elasticsearch datasource.

The graph shows the following metrics for HTTP requests to the URL path "/login":
- number of successful requests resulted in a HTTP response code between 200-300
- number of failed requests resulted in a HTTP response code between 400-500,
- Max. response time per point of time of HTTP requests
"""

from grafanalib import core, elasticsearch

suc_label = "Success (200-300)"
clt_err_label = "Client Errors (400-500)"
resptime_label = "Max response time"

filters = [
    core.Filter(query="response: [200 TO 300]", label=suc_label),
    core.Filter(query="response: [400 TO 500]", label=clt_err_label),
]

tgts = [
    elasticsearch.ElasticsearchTarget(
        query='request: "/login"',
        bucketAggs=[
            elasticsearch.FiltersGroupBy(filters=filters),
            elasticsearch.DateHistogramGroupBy(interval="10m"),
        ],
    ).auto_bucket_agg_ids(),
    elasticsearch.ElasticsearchTarget(
        query='request: "/login"',
        metricAggs=[elasticsearch.MaxMetricAgg(field="resptime")],
        alias=resptime_label,
    ).auto_bucket_agg_ids(),
]

g = core.Graph(
    title="login requests",
    dataSource="elasticsearch",
    targets=tgts,
    lines=False,
    legend=core.Legend(alignAsTable=True, rightSide=True, total=True, current=True, max=True),
    lineWidth=1,
    nullPointMode=core.NULL_AS_NULL,
    seriesOverrides=[
        {
            "alias": suc_label,
            "bars": True,
            "lines": False,
            "stack": "A",
            "yaxis": 1,
            "color": "#629E51",
        },
        {
            "alias": clt_err_label,
            "bars": True,
            "lines": False,
            "stack": "A",
            "yaxis": 1,
            "color": "#E5AC0E",
        },
        {
            "alias": resptime_label,
            "lines": True,
            "fill": 0,
            "nullPointMode": "connected",
            "steppedLine": True,
            "yaxis": 2,
            "color": "#447EBC",
        },
    ],
    yAxes=[
        core.YAxis(label="Count", format=core.SHORT_FORMAT, decimals=0),
        core.YAxis(label="Response Time", format=core.SECONDS_FORMAT, decimals=2),
    ],
    transparent=True,
    span=12,
)

dashboard = core.Dashboard(title="HTTP dashboard", rows=[core.Row(panels=[g])])
