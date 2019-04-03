"""Support for OpenTSDB."""

import attr
from attr.validators import instance_of
from grafanalib.core import Enum


class Aggregator(Enum):
    AVG = "avg"
    COUNT = "count"
    DEV = "dev"
    EP50R3 = "ep50r3"
    EP50R7 = "ep50r7"
    EP75R3 = "ep75r3"
    EP75R7 = "ep75r7"
    EP90R3 = "ep90r3"
    EP90R7 = "ep90r7"
    EP95R3 = "ep95r3"
    EP95R7 = "ep95r7"
    EP99R3 = "ep99r3"
    EP99R7 = "ep99r7"
    EP999R3 = "ep999r3"
    EP999R7 = "ep999r7"
    FIRST = "first"
    LAST = "last"
    MIMMIN = "mimmin"
    MIMMAX = "mimmax"
    MIN = "min"
    MAX = "max"
    NONE = "none"
    P50 = "p50"
    P75 = "p75"
    P90 = "p90"
    P95 = "p95"
    P99 = "p99"
    P999 = "p999"
    SUM = "sum"
    ZIMSUM = "zimsum"


class DownsamplingPolicy(Enum):
    NONE = "none"
    NAN = "nan"
    NULL = "null"
    ZERO = "zero"


DEFAULT_DOWNSAMPLING_FILL_POLICY = DownsamplingPolicy.NONE


class QueryFilter(Enum):
    LITERAL_OR = "literal_or"
    ILITERAL_OR = "iliteral_or"
    NOT_LITERAL_OR = "not_literal_or"
    NOT_ILITERAL_OR = "not_iliteral_or"
    WILDCARD = "wildcard"
    IWILDCARD = "iwildcard"
    REGEXP = "regexp"


DEFAULT_QUERY_FILTER = QueryFilter.LITERAL_OR


@attr.s(frozen=True)
class OpenTSDBFilter:

    value = attr.ib()
    tag = attr.ib()
    type = attr.ib(default=DEFAULT_QUERY_FILTER, validator=instance_of(QueryFilter))
    groupBy = attr.ib(default=False, validator=instance_of(bool))

    def to_json_data(self):
        return {"filter": self.value, "tagk": self.tag, "type": self.type, "groupBy": self.groupBy}


@attr.s(frozen=True)
class OpenTSDBTarget:
    """Generates OpenTSDB target JSON structure.

    Grafana docs on using OpenTSDB:
    http://docs.grafana.org/features/datasources/opentsdb/
    OpenTSDB docs on querying or reading data:
    http://opentsdb.net/docs/build/html/user_guide/query/index.html


    :param metric: OpenTSDB metric name
    :param refId: target reference id
    :param aggregator: defines metric aggregator.
        The list of opentsdb aggregators:
        http://opentsdb.net/docs/build/html/user_guide/query/aggregators.html#available-aggregators
    :param alias: legend alias. Use patterns like $tag_tagname to replace part
        of the alias for a tag value.
    :param isCounter: defines if rate function results should
        be interpret as counter
    :param counterMax: defines rate counter max value
    :param counterResetValue: defines rate counter reset value
    :param disableDownsampling: defines if downsampling should be disabled.
        OpenTSDB docs on downsampling:
        http://opentsdb.net/docs/build/html/user_guide/query/index.html#downsampling
    :param downsampleAggregator: defines downsampling aggregator
    :param downsampleFillPolicy: defines downsampling fill policy
    :param downsampleInterval: defines downsampling interval
    :param filters: defines the list of metric query filters.
        OpenTSDB docs on filters:
        http://opentsdb.net/docs/build/html/user_guide/query/index.html#filters
    :param shouldComputeRate: defines if rate function should be used.
        OpenTSDB docs on rate function:
        http://opentsdb.net/docs/build/html/user_guide/query/index.html#rate
    :param currentFilterGroupBy: defines if grouping should be enabled for
        current filter
    :param currentFilterKey: defines current filter key
    :param currentFilterType: defines current filter type
    :param currentFilterValue: defines current filter value
    """

    metric = attr.ib()
    refId = attr.ib(default="")
    aggregator = attr.ib(default="sum")
    alias = attr.ib(default=None)
    isCounter = attr.ib(default=False, validator=instance_of(bool))
    counterMax = attr.ib(default=None)
    counterResetValue = attr.ib(default=None)
    disableDownsampling = attr.ib(default=False, validator=instance_of(bool))
    downsampleAggregator = attr.ib(default=Aggregator.SUM)
    downsampleFillPolicy = attr.ib(
        default=DEFAULT_DOWNSAMPLING_FILL_POLICY, validator=instance_of(DownsamplingPolicy)
    )
    downsampleInterval = attr.ib(default=None)
    filters = attr.ib(default=attr.Factory(list))
    shouldComputeRate = attr.ib(default=False, validator=instance_of(bool))
    currentFilterGroupBy = attr.ib(default=False, validator=instance_of(bool))
    currentFilterKey = attr.ib(default="")
    currentFilterType = attr.ib(default=DEFAULT_QUERY_FILTER)
    currentFilterValue = attr.ib(default="")

    def to_json_data(self):

        return {
            "aggregator": self.aggregator,
            "alias": self.alias,
            "isCounter": self.isCounter,
            "counterMax": self.counterMax,
            "counterResetValue": self.counterResetValue,
            "disableDownsampling": self.disableDownsampling,
            "downsampleAggregator": self.downsampleAggregator,
            "downsampleFillPolicy": self.downsampleFillPolicy,
            "downsampleInterval": self.downsampleInterval,
            "filters": self.filters,
            "metric": self.metric,
            "refId": self.refId,
            "shouldComputeRate": self.shouldComputeRate,
            "currentFilterGroupBy": self.currentFilterGroupBy,
            "currentFilterKey": self.currentFilterKey,
            "currentFilterType": self.currentFilterType,
            "currentFilterValue": self.currentFilterValue,
        }
