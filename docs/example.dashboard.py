from grafanalib import core

dashboard = core.Dashboard(
    title="Frontend Stats",
    rows=[
        core.Row(
            panels=[
                core.Graph(
                    title="Frontend QPS",
                    dataSource="My Prometheus",
                    targets=[
                        core.Target(
                            expr='sum(irate(nginx_http_requests_total{job="default/frontend",status=~"1.."}[1m]))',
                            legendFormat="1xx",
                            refId="A",
                        ),
                        core.Target(
                            expr='sum(irate(nginx_http_requests_total{job="default/frontend",status=~"2.."}[1m]))',
                            legendFormat="2xx",
                            refId="B",
                        ),
                        core.Target(
                            expr='sum(irate(nginx_http_requests_total{job="default/frontend",status=~"3.."}[1m]))',
                            legendFormat="3xx",
                            refId="C",
                        ),
                        core.Target(
                            expr='sum(irate(nginx_http_requests_total{job="default/frontend",status=~"4.."}[1m]))',
                            legendFormat="4xx",
                            refId="D",
                        ),
                        core.Target(
                            expr='sum(irate(nginx_http_requests_total{job="default/frontend",status=~"5.."}[1m]))',
                            legendFormat="5xx",
                            refId="E",
                        ),
                    ],
                    yAxes=[
                        core.YAxis(format=core.OPS_FORMAT),
                        core.YAxis(format=core.SHORT_FORMAT),
                    ],
                    alert=core.Alert(
                        name="Too many 500s on Nginx",
                        message="More than 5 QPS of 500s on Nginx for 5 minutes",
                        alertConditions=[
                            core.AlertCondition(
                                core.Target(
                                    expr='sum(irate(nginx_http_requests_total{job="default/frontend",status=~"5.."}[1m]))',
                                    legendFormat="5xx",
                                    refId="A",
                                ),
                                timeRange=core.TimeRange("5m", "now"),
                                evaluator=core.GreaterThan(5),
                                operator=core.OP_AND,
                                reducerType=core.RTYPE_SUM,
                            )
                        ],
                    ),
                ),
                core.Graph(
                    title="Frontend latency",
                    dataSource="My Prometheus",
                    targets=[
                        core.Target(
                            expr='histogram_quantile(0.5, sum(irate(nginx_http_request_duration_seconds_bucket{job="default/frontend"}[1m])) by (le))',
                            legendFormat="0.5 quantile",
                            refId="A",
                        ),
                        core.Target(
                            expr='histogram_quantile(0.99, sum(irate(nginx_http_request_duration_seconds_bucket{job="default/frontend"}[1m])) by (le))',
                            legendFormat="0.99 quantile",
                            refId="B",
                        ),
                    ],
                    yAxes=core.single_y_axis(format=core.SECONDS_FORMAT),
                ),
            ]
        )
    ],
).auto_panel_ids()
