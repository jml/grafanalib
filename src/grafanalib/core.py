"""Low-level functions for building Grafana dashboards.

The functions in this module don't enforce Weaveworks policy, and only mildly
encourage it by way of some defaults. Rather, they are ways of building
arbitrary Grafana JSON.
"""

import enum
import itertools
import math
import warnings
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Type, TypeVar, Union

import attr
from attr.validators import instance_of
from typing_extensions import Protocol


def union(dicts: List[Dict[Any, Any]]) -> Dict[Any, Any]:
    """Merge dictionaries.

    Keys in later dictionaries overwrite keys in earlier ones.
    If an empty list is provided, return an empty dictionary.
    """
    if not dicts:
        return {}
    ret = dict(dicts[0])
    for d in dicts[1:]:
        ret.update(d)
    return ret


@attr.s(auto_attribs=True, frozen=True)
class RGBA:
    r: int
    g: int
    b: int
    a: float

    def to_json_data(self):
        return "rgba({}, {}, {}, {})".format(self.r, self.g, self.b, self.a)


@attr.s(auto_attribs=True, frozen=True)
class RGB:
    r: int
    g: int
    b: int

    def to_json_data(self):
        return "rgb({}, {}, {})".format(self.r, self.g, self.b)


@attr.s(auto_attribs=True, frozen=True)
class Pixels:
    num: int

    def to_json_data(self):
        return "{}px".format(self.num)


@attr.s(auto_attribs=True, frozen=True)
class Percent:
    num: float = 100.0

    def to_json_data(self):
        return "{}%".format(self.num)


class Enum(enum.Enum):
    """Restricted set of scalars."""

    def to_json_data(self):
        return self.value


class TooltipValueType(Enum):
    INDIVIDUAL = "individual"
    CUMULATIVE = "cumulative"


class NullPointMode(Enum):
    CONNECTED = "connected"
    AS_ZERO = "null as zero"
    AS_NULL = "null"


class Renderer(Enum):
    FLOT = "flot"


class PanelType(Enum):
    ABSOLUTE = "absolute"
    ALERTLIST = "alertlist"
    DASHBOARD = "dashboard"
    GRAPH = "graph"
    SINGLESTAT = "singlestat"
    TABLE = "table"
    TEXT = "text"


class DashboardStyle(Enum):
    DARK = "dark"
    LIGHT = "light"


class NumberFormat(Enum):
    DURATION = "dtdurations"
    NO = "none"
    OPS = "ops"
    PERCENT_UNIT = "percentunit"
    DAYS = "d"
    HOURS = "h"
    MINUTES = "m"
    SECONDS = "s"
    MILLISECONDS = "ms"
    SHORT = "short"
    BYTES = "bytes"
    BITS_PER_SEC = "bps"
    BYTES_PER_SEC = "Bps"


class AlertRuleState(Enum):
    NO_DATA = "no_data"
    ALERTING = "alerting"
    KEEP_LAST_STATE = "keep_state"


class EvaluatorType(Enum):
    GT = "gt"
    LT = "lt"
    WITHIN_RANGE = "within_range"
    OUTSIDE_RANGE = "outside_range"
    NO_VALUE = "no_value"


class ReducerType(Enum):
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    SUM = "sum"
    COUNT = "count"
    LAST = "last"
    MEDIAN = "median"


class ConditionType(Enum):
    QUERY = "query"


class Operator(Enum):
    AND = "and"
    OR = "or"


class TextMode(Enum):
    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"


class DatasourcePlugin(Enum):  # TODO: Double check this name
    GRAPHITE = "graphite"
    PROMETHEUS = "prometheus"
    INFLUXDB = "influxdb"
    OPENTSDB = "opentsdb"
    ELASTICSEARCH = "elasticsearch"
    CLOUDWATCH = "cloudwatch"


class TargetFormat(Enum):
    TIME_SERIES = "time_series"
    TABLE = "table"


class Transform(Enum):  # TODO: Double check this name
    AGGREGATIONS = "timeseries_aggregations"
    ANNOTATIONS = "annotations"
    COLUMNS = "timeseries_to_columns"
    JSON = "json"
    ROWS = "timeseries_to_rows"
    TABLE = "table"


class AlertListShow(Enum):
    CURRENT = "current"
    CHANGES = "changes"


class AlertListState(Enum):
    OK = "ok"
    PAUSED = "paused"
    NO_DATA = "no_data"
    EXECUTION_ERROR = "execution_error"
    ALERTING = "alerting"


class SortOrder(Enum):
    ASC = 1
    DESC = 2
    IMPORTANCE = 3


class Refresh(Enum):
    NEVER = 0
    ON_DASHBOARD_LOAD = 1
    ON_TIME_RANGE_CHANGE = 2


class TemplateHide(Enum):  # TODO: Double check this name
    SHOW = 0
    HIDE_LABEL = 1
    HIDE_VARIABLE = 2


class MappingType(Enum):
    VALUE_TO_TEXT = 1
    RANGE_TO_TEXT = 2


@attr.s(auto_attribs=True, frozen=True)
class Mapping:

    name: str
    value: MappingType

    def to_json_data(self):
        return {"name": self.name, "value": self.value}


MAPPING_VALUE_TO_TEXT = Mapping("value to text", MappingType.VALUE_TO_TEXT)
MAPPING_RANGE_TO_TEXT = Mapping("range to text", MappingType.RANGE_TO_TEXT)


class ValueType(Enum):
    MIN = "min"
    MAX = "max"
    AVG = "avg"
    CURR = "current"
    TOTAL = "total"
    NAME = "name"
    FIRST = "first"
    DELTA = "delta"
    RANGE = "range"


GREY1 = RGBA(216, 200, 27, 0.27)
GREY2 = RGBA(234, 112, 112, 0.22)
BLUE_RGBA = RGBA(31, 118, 189, 0.18)
BLUE_RGB = RGB(31, 120, 193)
GREEN = RGBA(50, 172, 45, 0.97)
ORANGE = RGBA(237, 129, 40, 0.89)
RED = RGBA(245, 54, 54, 0.9)
BLANK = RGBA(0, 0, 0, 0.0)

DEFAULT_FILL = 1
DEFAULT_REFRESH = "10s"
DEFAULT_ROW_HEIGHT = Pixels(250)
DEFAULT_LINE_WIDTH = 2
DEFAULT_POINT_RADIUS = 5
DEFAULT_RENDERER = Renderer.FLOT
DEFAULT_STEP = 10
DEFAULT_LIMIT = 10
TOTAL_SPAN = 12

UTC = "utc"

SCHEMA_VERSION = 12

DEFAULT_VALUE_TYPE = ValueType.AVG


@attr.s(auto_attribs=True, frozen=True)
class Grid:

    threshold1: Optional[float] = None
    threshold1Color: RGBA = GREY1
    threshold2: Optional[float] = None
    threshold2Color: RGBA = GREY2

    def to_json_data(self):
        return {
            "threshold1": self.threshold1,
            "threshold1Color": self.threshold1Color,
            "threshold2": self.threshold2,
            "threshold2Color": self.threshold2Color,
        }


@attr.s(auto_attribs=True, frozen=True)
class Panel:
    """Common properties for all panels."""

    # XXX: Should this be a base class or a component?

    title: str
    id: Optional[str] = None
    span: Optional[int] = None  # XXX: Not on AlertList
    transparent: bool = False
    editable: bool = True
    links: List[Any] = attr.Factory(list)  # TODO: What type are links?
    height: Optional[int] = None  # TODO: What type is height? Not relevant in post-5.0 world.
    description: Optional[str] = None

    # error: bool = False
    # minSpan: Optional[int]

    def to_json_data(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "id": self.id,
            "links": self.links,
            "span": self.span,
            "transparent": self.transparent,
            "editable": self.editable,
            "height": self.height,
            "description": self.description,
        }


@attr.s(frozen=True)
class Legend:
    avg = attr.ib(default=False, validator=instance_of(bool))
    current = attr.ib(default=False, validator=instance_of(bool))
    max = attr.ib(default=False, validator=instance_of(bool))
    min = attr.ib(default=False, validator=instance_of(bool))
    show = attr.ib(default=True, validator=instance_of(bool))
    total = attr.ib(default=False, validator=instance_of(bool))
    values = attr.ib(default=None)
    alignAsTable = attr.ib(default=False, validator=instance_of(bool))
    hideEmpty = attr.ib(default=False, validator=instance_of(bool))
    hideZero = attr.ib(default=False, validator=instance_of(bool))
    rightSide = attr.ib(default=False, validator=instance_of(bool))
    sideWidth = attr.ib(default=None)
    sort = attr.ib(default=None)
    sortDesc = attr.ib(default=False)

    def to_json_data(self):
        values = (
            (self.avg or self.current or self.max or self.min)
            if self.values is None
            else self.values
        )

        return {
            "avg": self.avg,
            "current": self.current,
            "max": self.max,
            "min": self.min,
            "show": self.show,
            "total": self.total,
            "values": values,
            "alignAsTable": self.alignAsTable,
            "hideEmpty": self.hideEmpty,
            "hideZero": self.hideZero,
            "rightSide": self.rightSide,
            "sideWidth": self.sideWidth,
            "sort": self.sort,
            "sortDesc": self.sortDesc,
        }


@attr.s(frozen=True)
class Target:
    """
    Metric to show.

    :param target: Graphite way to select data
    """

    expr = attr.ib(default="")
    format = attr.ib(default=TargetFormat.TIME_SERIES)
    legendFormat = attr.ib(default="")
    interval = attr.ib(default="", validator=instance_of(str))
    intervalFactor = attr.ib(default=2)
    metric = attr.ib(default="")
    refId = attr.ib(default="")
    step = attr.ib(default=DEFAULT_STEP)
    target = attr.ib(default="")
    instant = attr.ib(validator=instance_of(bool), default=False)
    datasource = attr.ib(default="")

    def to_json_data(self):
        return {
            "expr": self.expr,
            "target": self.target,
            "format": self.format,
            "interval": self.interval,
            "intervalFactor": self.intervalFactor,
            "legendFormat": self.legendFormat,
            "metric": self.metric,
            "refId": self.refId,
            "step": self.step,
            "instant": self.instant,
            "datasource": self.datasource,
        }


@attr.s(frozen=True)
class Tooltip:

    msResolution = attr.ib(default=True, validator=instance_of(bool))
    shared = attr.ib(default=True, validator=instance_of(bool))
    sort = attr.ib(default=0)
    valueType = attr.ib(default=TooltipValueType.CUMULATIVE)

    def to_json_data(self):
        return {
            "msResolution": self.msResolution,
            "shared": self.shared,
            "sort": self.sort,
            "value_type": self.valueType,
        }


def is_valid_xaxis_mode(_instance, attribute, value):  # TODO: Make this an Enum
    XAXIS_MODES = ("time", "series")
    if value not in XAXIS_MODES:
        raise ValueError(
            "{attr} should be one of {choice}".format(attr=attribute, choice=XAXIS_MODES)
        )


@attr.s(frozen=True)
class XAxis:

    mode = attr.ib(default="time", validator=is_valid_xaxis_mode)
    name = attr.ib(default=None)
    values = attr.ib(default=attr.Factory(list))
    show = attr.ib(validator=instance_of(bool), default=True)

    def to_json_data(self):
        return {"show": self.show}


@attr.s(frozen=True)
class YAxis:
    """A single Y axis.

    Grafana graphs have two Y axes: one on the left and one on the right.
    """

    decimals = attr.ib(default=None)
    format = attr.ib(default=None)
    label = attr.ib(default=None)
    logBase = attr.ib(default=1)
    max = attr.ib(default=None)
    min = attr.ib(default=0)
    show = attr.ib(default=True, validator=instance_of(bool))

    def to_json_data(self):
        return {
            "decimals": self.decimals,
            "format": self.format,
            "label": self.label,
            "logBase": self.logBase,
            "max": self.max,
            "min": self.min,
            "show": self.show,
        }


@attr.s(frozen=True)
class YAxes:
    """The pair of Y axes on a Grafana graph.

    Each graph has two Y Axes, a left one and a right one.
    """

    left = attr.ib(
        default=attr.Factory(lambda: YAxis(format=NumberFormat.SHORT)), validator=instance_of(YAxis)
    )
    right = attr.ib(
        default=attr.Factory(lambda: YAxis(format=NumberFormat.SHORT)), validator=instance_of(YAxis)
    )

    def to_json_data(self):
        return [self.left, self.right]


def single_y_axis(**kwargs):
    """Specify that a graph has a single Y axis.

    Parameters are those passed to `YAxis`. Returns a `YAxes` object (i.e. a
    pair of axes) that can be used as the yAxes parameter of a graph.
    """
    axis = YAxis(**kwargs)
    return YAxes(left=axis)


def to_y_axes(data: Union[YAxes, Tuple[Any, Any], List[Any]]) -> YAxes:
    """Backwards compatibility for 'YAxes'.

    In grafanalib 0.1.2 and earlier, Y axes were specified as a list of two
    elements. Now, we have a dedicated `YAxes` type.

    This function converts a list of two `YAxis` values to a `YAxes` value,
    silently passes through `YAxes` values, warns about doing things the old
    way, and errors when there are invalid values.
    """
    if isinstance(data, YAxes):
        return data
    if not isinstance(data, (list, tuple)):
        raise ValueError("Y axes must be either YAxes or a list of two values, got %r" % data)
    if len(data) != 2:
        raise ValueError("Must specify exactly two YAxes, got %d: %r" % (len(data), data))
    warnings.warn(
        "Specify Y axes using YAxes or single_y_axis, rather than a " "list/tuple",
        DeprecationWarning,
        stacklevel=3,
    )
    return YAxes(left=data[0], right=data[1])


# TODO: Add a Panel type and use that instead of Any.
def _balance_panels(panels: List[Panel]) -> List[Panel]:
    """Resize panels so they are evenly spaced."""
    allotted_spans = sum(panel.span if panel.span else 0 for panel in panels)
    no_span_set = [panel for panel in panels if panel.span is None]
    auto_span = math.ceil((TOTAL_SPAN - allotted_spans) / (len(no_span_set) or 1))
    return [attr.evolve(panel, span=auto_span) if panel.span is None else panel for panel in panels]


class HasPanel(Protocol):
    """A thing with a panel.

    TODO: Probably want to make Panel a parameterized type that has a visualization.
    """

    panel: Panel


def _balance_visualizations(vizs: Any) -> List[HasPanel]:
    """Resize visualizations so they are evenly spaced."""
    panels = _balance_panels([v.panel for v in vizs])
    return [attr.evolve(viz, panel=panel) for viz, panel in zip(vizs, panels)]


RowT = TypeVar("RowT", bound="Row")


@attr.s(auto_attribs=True, frozen=True)
class Row:
    # XXX: Grafana 5.0 and later doesn't use Row anymore.
    # TODO: jml would like to separate the balancing behaviour from this
    # layer.
    panels: List[HasPanel] = attr.ib(default=attr.Factory(list), converter=_balance_visualizations)
    collapse: bool = False
    editable: bool = True
    height: Pixels = DEFAULT_ROW_HEIGHT
    showTitle: Optional[bool] = None
    title: Optional[str] = None
    repeat: Optional[Any] = None  # TODO: What type is this?

    def iter_panels(self) -> Iterable[Panel]:
        return (p.panel for p in self.panels)

    def map_panels(self: RowT, f: Callable[[Panel], Panel]) -> RowT:
        panels = map(f, self.iter_panels())
        with_panels = [attr.evolve(p, panel=panel) for p, panel in zip(self.panels, panels)]
        return attr.evolve(self, panels=with_panels)

    def to_json_data(self) -> Dict[str, Any]:
        showTitle = False
        title = "New row"
        if self.title is not None:
            showTitle = True
            title = self.title
        if self.showTitle is not None:
            showTitle = self.showTitle
        return {
            "collapse": self.collapse,
            "editable": self.editable,
            "height": self.height,
            "panels": self.panels,
            "showTitle": showTitle,
            "title": title,
            "repeat": self.repeat,
        }


@attr.s(frozen=True)
class Annotations:
    list = attr.ib(default=attr.Factory(list))

    def to_json_data(self):
        return {"list": self.list}


@attr.s(frozen=True)
class DataSourceInput:
    name = attr.ib()
    label = attr.ib()
    pluginId = attr.ib()
    pluginName = attr.ib()
    description = attr.ib(default="", validator=instance_of(str))

    def to_json_data(self):
        return {
            "description": self.description,
            "label": self.label,
            "name": self.name,
            "pluginId": self.pluginId,
            "pluginName": self.pluginName,
            "type": "datasource",
        }


@attr.s(frozen=True)
class ConstantInput:
    name = attr.ib()
    label = attr.ib()
    value = attr.ib()
    description = attr.ib(default="", validator=instance_of(str))

    def to_json_data(self):
        return {
            "description": self.description,
            "label": self.label,
            "name": self.name,
            "type": "constant",
            "value": self.value,
        }


@attr.s(frozen=True)
class DashboardLink:
    dashboard = attr.ib()
    uri = attr.ib()
    keepTime = attr.ib(default=True, validator=instance_of(bool))
    title = attr.ib(default=None)
    type = attr.ib(default=PanelType.DASHBOARD)

    def to_json_data(self):
        title = self.dashboard if self.title is None else self.title
        return {
            "dashUri": self.uri,
            "dashboard": self.dashboard,
            "keepTime": self.keepTime,
            "title": title,
            "type": self.type.to_json_data(),
            "url": self.uri,
        }


@attr.s(frozen=True)
class ExternalLink:
    """ExternalLink creates a top-level link attached to a dashboard.

        :param url: the URL to link to
        :param title: the text of the link
        :param keepTime: if true, the URL params for the dashboard's
            current time period are appended
    """

    uri = attr.ib()
    title = attr.ib()
    keepTime = attr.ib(default=False, validator=instance_of(bool))

    def to_json_data(self):
        return {"keepTime": self.keepTime, "title": self.title, "type": "link", "url": self.uri}


@attr.s(frozen=True)
class Template:
    """Template create a new 'variable' for the dashboard, defines the variable
    name, human name, query to fetch the values and the default value.

        :param default: the default value for the variable
        :param dataSource: where to fetch the values for the variable from
        :param label: the variable's human label
        :param name: the variable's name
        :param query: the query users to fetch the valid values of the variable
        :param refresh: Controls when to update values in the dropdown
        :param allValue: specify a custom all value with regex,
            globs or lucene syntax.
        :param includeAll: Add a special All option whose value includes
            all options.
        :param regex: Regex to filter or capture specific parts of the names
            return by your data source query.
        :param multi: If enabled, the variable will support the selection of
            multiple options at the same time.
        :param type: The template type, can be one of: query (default),
            interval, datasource, custom, constant, adhoc.
        :param hide: Hide this variable in the dashboard, can be one of:
            SHOW (default), HIDE_LABEL, HIDE_VARIABLE
    """

    name = attr.ib()
    query = attr.ib()
    default = attr.ib(default=None)
    dataSource = attr.ib(default=None)
    label = attr.ib(default=None)
    allValue = attr.ib(default=None)
    includeAll = attr.ib(default=False, validator=instance_of(bool))
    multi = attr.ib(default=False, validator=instance_of(bool))
    regex = attr.ib(default=None)
    useTags = attr.ib(default=False, validator=instance_of(bool))
    tagsQuery = attr.ib(default=None)
    tagValuesQuery = attr.ib(default=None)
    refresh = attr.ib(default=Refresh.ON_DASHBOARD_LOAD, validator=instance_of(Refresh))
    type = attr.ib(default="query")
    hide = attr.ib(default=TemplateHide.SHOW)

    def to_json_data(self):
        return {
            "allValue": self.allValue,
            "current": {"text": self.default, "value": self.default, "tags": []},
            "datasource": self.dataSource,
            "hide": self.hide,
            "includeAll": self.includeAll,
            "label": self.label,
            "multi": self.multi,
            "name": self.name,
            "options": [],
            "query": self.query,
            "refresh": self.refresh,
            "regex": self.regex,
            "sort": 1,
            "type": self.type,
            "useTags": self.useTags,
            "tagsQuery": self.tagsQuery,
            "tagValuesQuery": self.tagValuesQuery,
        }


@attr.s(frozen=True)
class Templating:
    list = attr.ib(default=attr.Factory(list))

    def to_json_data(self):
        return {"list": self.list}


@attr.s(frozen=True)
class Time:
    start = attr.ib()
    end = attr.ib()

    def to_json_data(self):
        return {"from": self.start, "to": self.end}


DEFAULT_TIME = Time("now-1h", "now")


@attr.s(frozen=True)
class TimePicker:
    refreshIntervals = attr.ib()
    timeOptions = attr.ib()

    def to_json_data(self):
        return {"refresh_intervals": self.refreshIntervals, "time_options": self.timeOptions}


DEFAULT_TIME_PICKER = TimePicker(
    refreshIntervals=["5s", "10s", "30s", "1m", "5m", "15m", "30m", "1h", "2h", "1d"],
    timeOptions=["5m", "15m", "1h", "6h", "12h", "24h", "2d", "7d", "30d"],
)


@attr.s(frozen=True)
class Evaluator:
    type = attr.ib()
    params = attr.ib()

    def to_json_data(self):
        return {"type": self.type, "params": self.params}


def GreaterThan(value):
    return Evaluator(EvaluatorType.GT, [value])


def LowerThan(value):
    return Evaluator(EvaluatorType.LT, [value])


def WithinRange(from_value, to_value):
    return Evaluator(EvaluatorType.WITHIN_RANGE, [from_value, to_value])


def OutsideRange(from_value, to_value):
    return Evaluator(EvaluatorType.OUTSIDE_RANGE, [from_value, to_value])


def NoValue():
    return Evaluator(EvaluatorType.NO_VALUE, [])


@attr.s(frozen=True)
class TimeRange:
    """A time range for an alert condition.

    A condition has to hold for this length of time before triggering.

    :param str from_time: Either a number + unit (s: second, m: minute,
        h: hour, etc)  e.g. ``"5m"`` for 5 minutes, or ``"now"``.
    :param str to_time: Either a number + unit (s: second, m: minute,
        h: hour, etc)  e.g. ``"5m"`` for 5 minutes, or ``"now"``.
    """

    from_time = attr.ib()
    to_time = attr.ib()

    def to_json_data(self):
        return [self.from_time, self.to_time]


@attr.s(frozen=True)
class AlertCondition:
    """
    A condition on an alert.

    :param Target target: Metric the alert condition is based on.
    :param Evaluator evaluator: How we decide whether we should alert on the
        metric. e.g. ``GreaterThan(5)`` means the metric must be greater than 5
        to trigger the condition. See ``GreaterThan``, ``LowerThan``,
        ``WithinRange``, ``OutsideRange``, ``NoValue``.
    :param TimeRange timeRange: How long the condition must be true for before
        we alert.
    :param operator: One of ``OP_AND`` or ``OP_OR``. How this condition
        combines with other conditions.
    :param reducerType: RTYPE_*
    :param type: CTYPE_*
    """

    target = attr.ib(validator=instance_of(Target))
    evaluator = attr.ib(validator=instance_of(Evaluator))
    timeRange = attr.ib(validator=instance_of(TimeRange))
    operator = attr.ib()
    reducerType = attr.ib()
    type = attr.ib(default=ConditionType.QUERY)

    def to_json_data(self):
        queryParams = [self.target.refId, self.timeRange.from_time, self.timeRange.to_time]
        return {
            "evaluator": self.evaluator,
            "operator": {"type": self.operator},
            "query": {"model": self.target, "params": queryParams},
            "reducer": {"params": [], "type": self.reducerType},
            "type": self.type,
        }


@attr.s(frozen=True)
class Alert:

    name = attr.ib()
    message = attr.ib()
    alertConditions = attr.ib()
    executionErrorState = attr.ib(default=AlertRuleState.ALERTING)
    frequency = attr.ib(default="60s")
    handler = attr.ib(default=1)
    noDataState = attr.ib(default=AlertRuleState.NO_DATA)
    notifications = attr.ib(default=attr.Factory(list))

    def to_json_data(self):
        return {
            "conditions": self.alertConditions,
            "executionErrorState": self.executionErrorState,
            "frequency": self.frequency,
            "handler": self.handler,
            "message": self.message,
            "name": self.name,
            "noDataState": self.noDataState,
            "notifications": self.notifications,
        }


DashboardT = TypeVar("DashboardT", bound="Dashboard")


@attr.s(frozen=True)
class Dashboard:

    title = attr.ib()
    rows = attr.ib()
    annotations = attr.ib(default=attr.Factory(Annotations), validator=instance_of(Annotations))
    editable = attr.ib(default=True, validator=instance_of(bool))
    gnetId = attr.ib(default=None)
    hideControls = attr.ib(default=False, validator=instance_of(bool))
    id = attr.ib(default=None)
    inputs = attr.ib(default=attr.Factory(list))
    links = attr.ib(default=attr.Factory(list))
    refresh = attr.ib(default=DEFAULT_REFRESH)
    schemaVersion = attr.ib(default=SCHEMA_VERSION)
    sharedCrosshair = attr.ib(default=False, validator=instance_of(bool))
    style = attr.ib(default=DashboardStyle.DARK)
    tags = attr.ib(default=attr.Factory(list))
    templating = attr.ib(default=attr.Factory(Templating), validator=instance_of(Templating))
    time = attr.ib(default=attr.Factory(lambda: DEFAULT_TIME), validator=instance_of(Time))
    timePicker = attr.ib(
        default=attr.Factory(lambda: DEFAULT_TIME_PICKER), validator=instance_of(TimePicker)
    )
    timezone = attr.ib(default=UTC)
    version = attr.ib(default=0)
    uid = attr.ib(default=None)

    def iter_panels(self) -> Iterable[Panel]:
        for row in self.rows:
            for panel in row.iter_panels():
                yield panel

    def map_panels(self: DashboardT, f: Callable[[Panel], Panel]) -> DashboardT:
        return attr.evolve(self, rows=[r.map_panels(f) for r in self.rows])

    def auto_panel_ids(self: DashboardT) -> DashboardT:
        """Give unique IDs all the panels without IDs.

        Returns a new ``Dashboard`` that is the same as this one, except all
        of the panels have their ``id`` property set. Any panels which had an
        ``id`` property set will keep that property, all others will have
        auto-generated IDs provided for them.
        """
        ids = {panel.id for panel in self.iter_panels() if panel.id}
        auto_ids = (i for i in itertools.count(1) if i not in ids)

        def set_id(panel):
            return panel if panel.id else attr.evolve(panel, id=next(auto_ids))

        return self.map_panels(set_id)

    def to_json_data(self) -> Dict[str, Any]:
        return {
            "__inputs": self.inputs,
            "annotations": self.annotations,
            "editable": self.editable,
            "gnetId": self.gnetId,
            "hideControls": self.hideControls,
            "id": self.id,
            "links": self.links,
            "refresh": self.refresh,
            "rows": self.rows,
            "schemaVersion": self.schemaVersion,
            "sharedCrosshair": self.sharedCrosshair,
            "style": self.style,
            "tags": self.tags,
            "templating": self.templating,
            "title": self.title,
            "time": self.time,
            "timepicker": self.timePicker,
            "timezone": self.timezone,
            "version": self.version,
            "uid": self.uid,
        }


@attr.s(frozen=True)
class Graph:
    """
    Generates Graph panel json structure.

    :param dataSource: DataSource's name
    :param minSpan: Minimum width for each panel
    :param repeat: Template's name to repeat Graph on
    """

    panel = attr.ib(validator=instance_of(Panel))
    targets = attr.ib()
    aliasColors = attr.ib(default=attr.Factory(dict))
    bars = attr.ib(default=False, validator=instance_of(bool))
    dataSource = attr.ib(default=None)
    error = attr.ib(default=False, validator=instance_of(bool))
    fill = attr.ib(default=1, validator=instance_of(int))
    grid = attr.ib(default=attr.Factory(Grid), validator=instance_of(Grid))
    isNew = attr.ib(default=True, validator=instance_of(bool))
    legend = attr.ib(default=attr.Factory(Legend), validator=instance_of(Legend))
    lines = attr.ib(default=True, validator=instance_of(bool))
    lineWidth = attr.ib(default=DEFAULT_LINE_WIDTH)
    minSpan = attr.ib(default=None)
    nullPointMode = attr.ib(default=NullPointMode.CONNECTED)
    percentage = attr.ib(default=False, validator=instance_of(bool))
    pointRadius = attr.ib(default=DEFAULT_POINT_RADIUS)
    points = attr.ib(default=False, validator=instance_of(bool))
    renderer = attr.ib(default=DEFAULT_RENDERER)
    repeat = attr.ib(default=None)
    seriesOverrides = attr.ib(default=attr.Factory(list))
    stack = attr.ib(default=False, validator=instance_of(bool))
    steppedLine = attr.ib(default=False, validator=instance_of(bool))
    timeFrom = attr.ib(default=None)
    timeShift = attr.ib(default=None)
    tooltip = attr.ib(default=attr.Factory(Tooltip), validator=instance_of(Tooltip))
    xAxis = attr.ib(default=attr.Factory(XAxis), validator=instance_of(XAxis))
    # XXX: This isn't a *good* default, rather it's the default Grafana uses.
    yAxes = attr.ib(default=attr.Factory(YAxes), converter=to_y_axes, validator=instance_of(YAxes))
    alert = attr.ib(default=None)

    def to_json_data(self):
        graph_object = {
            "aliasColors": self.aliasColors,
            "bars": self.bars,
            "datasource": self.dataSource,
            "error": self.error,
            "fill": self.fill,
            "grid": self.grid,
            "isNew": self.isNew,
            "legend": self.legend,
            "lines": self.lines,
            "linewidth": self.lineWidth,
            "minSpan": self.minSpan,
            "nullPointMode": self.nullPointMode,
            "percentage": self.percentage,
            "pointradius": self.pointRadius,
            "points": self.points,
            "renderer": self.renderer,
            "repeat": self.repeat,
            "seriesOverrides": self.seriesOverrides,
            "stack": self.stack,
            "steppedLine": self.steppedLine,
            "targets": self.targets,
            "timeFrom": self.timeFrom,
            "timeShift": self.timeShift,
            "tooltip": self.tooltip,
            "xaxis": self.xAxis,
            "yaxes": self.yAxes,
        }
        alerts = {"alert": self.alert} if self.alert else {}
        return union([self.panel.to_json_data(), graph_object, alerts])


@attr.s(frozen=True)
class SparkLine:
    fillColor = attr.ib(default=attr.Factory(lambda: BLUE_RGBA), validator=instance_of(RGBA))
    full = attr.ib(default=False, validator=instance_of(bool))
    lineColor = attr.ib(default=attr.Factory(lambda: BLUE_RGB), validator=instance_of(RGB))
    show = attr.ib(default=False, validator=instance_of(bool))

    def to_json_data(self):
        return {
            "fillColor": self.fillColor,
            "full": self.full,
            "lineColor": self.lineColor,
            "show": self.show,
        }


@attr.s(frozen=True)
class ValueMap:
    op = attr.ib()
    text = attr.ib()
    value = attr.ib()

    def to_json_data(self):
        return {"op": self.op, "text": self.text, "value": self.value}


@attr.s(frozen=True)
class RangeMap:
    start = attr.ib()
    end = attr.ib()
    text = attr.ib()

    def to_json_data(self):
        return {"from": self.start, "to": self.end, "text": self.text}


@attr.s
class Gauge:

    minValue = attr.ib(default=0, validator=instance_of(int))
    maxValue = attr.ib(default=100, validator=instance_of(int))
    show = attr.ib(default=False, validator=instance_of(bool))
    thresholdLabels = attr.ib(default=False, validator=instance_of(bool))
    thresholdMarkers = attr.ib(default=True, validator=instance_of(bool))

    def to_json_data(self):
        return {
            "maxValue": self.maxValue,
            "minValue": self.minValue,
            "show": self.show,
            "thresholdLabels": self.thresholdLabels,
            "thresholdMarkers": self.thresholdMarkers,
        }


@attr.s(frozen=True)
class Text:
    """Generates a Text panel."""

    type = PanelType.TEXT

    panel = attr.ib(validator=instance_of(Panel))
    content = attr.ib()
    error = attr.ib(default=False, validator=instance_of(bool))
    mode = attr.ib(default=TextMode.MARKDOWN)

    def to_json_data(self):
        return union(
            [
                self.panel.to_json_data(),
                {"content": self.content, "error": self.error, "mode": self.mode},
            ]
        )


@attr.s(frozen=True)
class AlertList:
    """Generates the AlertList Panel."""

    type = PanelType.ALERTLIST

    panel = attr.ib(validator=instance_of(Panel))
    limit = attr.ib(default=DEFAULT_LIMIT)
    onlyAlertsOnDashboard = attr.ib(default=True, validator=instance_of(bool))
    show = attr.ib(default=AlertListShow.CURRENT, validator=instance_of(AlertListShow))
    sortOrder = attr.ib(default=SortOrder.ASC, validator=instance_of(SortOrder))
    stateFilter = attr.ib(default=attr.Factory(list))

    def to_json_data(self):
        return union(
            [
                self.panel.to_json_data(),
                {
                    "limit": self.limit,
                    "onlyAlertsOnDashboard": self.onlyAlertsOnDashboard,
                    "show": self.show,
                    "sortOrder": self.sortOrder,
                    "stateFilter": self.stateFilter,
                },
            ]
        )


@attr.s(frozen=True)
class SingleStat:
    """Generates Single Stat panel json structure

    Grafana doc on singlestat: http://docs.grafana.org/reference/singlestat/

    :param dataSource: Grafana datasource name
    :param targets: list of metric requests for chosen datasource
    :param cacheTimeout: metric query result cache ttl
    :param colors: the list of colors that can be used for coloring
        panel value or background. Additional info on coloring in docs:
        http://docs.grafana.org/reference/singlestat/#coloring
    :param colorBackground: defines if grafana will color panel background
    :param colorValue: defines if grafana will color panel value
    :param decimals: override automatic decimal precision for legend/tooltips
    :param format: defines value units
    :param gauge: draws and additional speedometer-like gauge based
    :param hideTimeOverride: hides time overrides
    :param interval: defines time interval between metric queries
    :param mappingType: defines panel mapping type.
        Additional info can be found in docs:
        http://docs.grafana.org/reference/singlestat/#value-to-text-mapping
    :param mappingTypes: the list of available mapping types for panel
    :param maxDataPoints: maximum metric query results,
        that will be used for rendering
    :param minSpan: minimum span number
    :param nullText: defines what to show if metric query result is undefined
    :param nullPointMode: defines how to render undefined values
    :param postfix: defines postfix that will be attached to value
    :param postfixFontSize: defines postfix font size
    :param prefix: defines prefix that will be attached to value
    :param prefixFontSize: defines prefix font size
    :param rangeMaps: the list of value to text mappings
    :param sparkline: defines if grafana should draw an additional sparkline.
        Sparkline grafana documentation:
        http://docs.grafana.org/reference/singlestat/#spark-lines
    :param thresholds: single stat thresholds
    :param valueFontSize: defines value font size
    :param valueName: defines value type. possible values are:
        min, max, avg, current, total, name, first, delta, range
    :param valueMaps: the list of value to text mappings
    :param timeFrom: time range that Override relative time
    """

    type = PanelType.SINGLESTAT
    panel = attr.ib(validator=instance_of(Panel))

    dataSource = attr.ib()
    targets = attr.ib()
    cacheTimeout = attr.ib(default=None)
    colors = attr.ib(default=attr.Factory(lambda: [GREEN, ORANGE, RED]))
    colorBackground = attr.ib(default=False, validator=instance_of(bool))
    colorValue = attr.ib(default=False, validator=instance_of(bool))
    decimals = attr.ib(default=None)
    format = attr.ib(default="none")
    gauge = attr.ib(default=attr.Factory(Gauge), validator=instance_of(Gauge))
    hideTimeOverride = attr.ib(default=False, validator=instance_of(bool))
    interval = attr.ib(default=None)
    mappingType = attr.ib(default=MappingType.VALUE_TO_TEXT)
    mappingTypes = attr.ib(
        default=attr.Factory(lambda: [MAPPING_VALUE_TO_TEXT, MAPPING_RANGE_TO_TEXT])
    )
    maxDataPoints = attr.ib(default=100)
    minSpan = attr.ib(default=None)
    nullText = attr.ib(default=None)
    nullPointMode = attr.ib(default="connected")
    postfix = attr.ib(default="")
    postfixFontSize = attr.ib(default="50%")
    prefix = attr.ib(default="")
    prefixFontSize = attr.ib(default="50%")
    rangeMaps = attr.ib(default=attr.Factory(list))
    repeat = attr.ib(default=None)
    sparkline = attr.ib(default=attr.Factory(SparkLine), validator=instance_of(SparkLine))
    thresholds = attr.ib(default="")
    valueFontSize = attr.ib(default="80%")
    valueName = attr.ib(default=DEFAULT_VALUE_TYPE)
    valueMaps = attr.ib(default=attr.Factory(list))
    timeFrom = attr.ib(default=None)

    def to_json_data(self) -> Dict[str, Any]:
        return union(
            [
                self.panel.to_json_data(),
                {
                    "cacheTimeout": self.cacheTimeout,
                    "colorBackground": self.colorBackground,
                    "colorValue": self.colorValue,
                    "colors": self.colors,
                    "datasource": self.dataSource,
                    "decimals": self.decimals,
                    "format": self.format,
                    "gauge": self.gauge,
                    "interval": self.interval,
                    "hideTimeOverride": self.hideTimeOverride,
                    "mappingType": self.mappingType,
                    "mappingTypes": self.mappingTypes,
                    "maxDataPoints": self.maxDataPoints,
                    "minSpan": self.minSpan,
                    "nullPointMode": self.nullPointMode,
                    "nullText": self.nullText,
                    "postfix": self.postfix,
                    "postfixFontSize": self.postfixFontSize,
                    "prefix": self.prefix,
                    "prefixFontSize": self.prefixFontSize,
                    "rangeMaps": self.rangeMaps,
                    "repeat": self.repeat,
                    "sparkline": self.sparkline,
                    "targets": self.targets,
                    "thresholds": self.thresholds,
                    "valueFontSize": self.valueFontSize,
                    "valueMaps": self.valueMaps,
                    "valueName": self.valueName,
                    "timeFrom": self.timeFrom,
                },
            ]
        )


@attr.s(frozen=True)
class DateColumnStyleType:
    TYPE = "date"

    dateFormat = attr.ib(default="YYYY-MM-DD HH:mm:ss")

    def to_json_data(self):
        return {"dateFormat": self.dateFormat, "type": self.TYPE}


@attr.s(frozen=True)
class NumberColumnStyleType:
    TYPE = "number"

    colorMode = attr.ib(default=None)
    colors = attr.ib(default=attr.Factory(lambda: [GREEN, ORANGE, RED]))
    thresholds = attr.ib(default=attr.Factory(list))
    decimals = attr.ib(default=2, validator=instance_of(int))
    unit = attr.ib(default=NumberFormat.SHORT)

    def to_json_data(self):
        return {
            "colorMode": self.colorMode,
            "colors": self.colors,
            "decimals": self.decimals,
            "thresholds": self.thresholds,
            "type": self.TYPE,
            "unit": self.unit,
        }


@attr.s(frozen=True)
class StringColumnStyleType:
    TYPE = "string"

    preserveFormat = attr.ib(validator=instance_of(bool))
    sanitize = attr.ib(validator=instance_of(bool))

    def to_json_data(self):
        return {"preserveFormat": self.preserveFormat, "sanitize": self.sanitize, "type": self.TYPE}


@attr.s(frozen=True)
class HiddenColumnStyleType:
    TYPE = "hidden"

    def to_json_data(self):
        return {"type": self.TYPE}


ColumnStyleTypes = Union[
    DateColumnStyleType, HiddenColumnStyleType, NumberColumnStyleType, StringColumnStyleType
]


@attr.s(auto_attribs=True, frozen=True)
class ColumnStyle:

    alias: str = ""
    pattern: str = ""
    type: ColumnStyleTypes = attr.Factory(NumberColumnStyleType)

    def to_json_data(self):
        data = {"alias": self.alias, "pattern": self.pattern}
        data.update(self.type.to_json_data())
        return data


@attr.s(frozen=True)
class ColumnSort:
    col = attr.ib(default=None)
    desc = attr.ib(default=False, validator=instance_of(bool))

    def to_json_data(self):
        return {"col": self.col, "desc": self.desc}


@attr.s(frozen=True)
class Column:
    """Details of an aggregation column in a table panel.

    :param text: name of column
    :param value: aggregation function
    """

    text = attr.ib(default="Avg")
    value = attr.ib(default="avg")

    def to_json_data(self):
        return {"text": self.text, "value": self.value}


def _style_columns(
    columns: List[Tuple[Column, Optional[ColumnStyle]]]
) -> Tuple[List[Column], List[ColumnStyle]]:
    """Generate a list of column styles given some styled columns.

    The 'Table' object in Grafana separates column definitions from column
    style definitions. However, when defining dashboards it can be very useful
    to define the style next to the column. This function helps that happen.

    :param columns: A list of (Column, ColumnStyle) pairs. The associated
        ColumnStyles must not have a 'pattern' specified. You can also provide
       'None' if you want to use the default styles.
    :return: A list of ColumnStyle values that can be used in a Grafana
        definition.
    """
    new_columns = []
    styles = []
    for column, style in columns:
        new_columns.append(column)
        if not style:
            continue
        if style.pattern and style.pattern != column.text:
            raise ValueError(
                "ColumnStyle pattern (%r) must match the column name (%r) if "
                "specified" % (style.pattern, column.text)
            )
        styles.append(attr.evolve(style, pattern=column.text))
    return new_columns, styles


TableT = TypeVar("TableT", bound="Table")


@attr.s(frozen=True)
class Table:
    """Generates Table panel json structure

    Grafana doc on table: http://docs.grafana.org/reference/table_panel/

    :param columns: table columns for Aggregations view
    :param dataSource: Grafana datasource name
    :param fontSize: defines value font size
    :param hideTimeOverride: hides time overrides
    :param minSpan: minimum span number
    :param pageSize: rows per page (None is unlimited)
    :param scroll: scroll the table instead of displaying in full
    :param showHeader: show the table header
    :param styles: defines formatting for each column
    :param targets: list of metric requests for chosen datasource
    :param timeFrom: time range that Override relative time
    :param transform: table style
    """

    type = PanelType.TABLE

    panel = attr.ib(validator=instance_of(Panel))
    dataSource = attr.ib()
    targets = attr.ib()
    columns = attr.ib(default=attr.Factory(list))
    fontSize = attr.ib(default="100%")
    hideTimeOverride = attr.ib(default=False, validator=instance_of(bool))
    minSpan = attr.ib(default=None)
    pageSize = attr.ib(default=None)
    repeat = attr.ib(default=None)
    scroll = attr.ib(default=True, validator=instance_of(bool))
    showHeader = attr.ib(default=True, validator=instance_of(bool))
    sort = attr.ib(default=attr.Factory(ColumnSort), validator=instance_of(ColumnSort))
    styles = attr.ib()
    timeFrom = attr.ib(default=None)
    transform = attr.ib(default=Transform.COLUMNS)

    @styles.default
    def styles_default(self):  # pylint: disable=no-self-use
        return [
            ColumnStyle(alias="Time", pattern="time", type=DateColumnStyleType()),
            ColumnStyle(pattern="/.*/"),
        ]

    @classmethod
    def with_styled_columns(
        cls: Type[TableT],
        columns: List[Tuple[Column, Optional[ColumnStyle]]],
        styles: Optional[List[ColumnStyle]] = None,
        **kwargs,
    ) -> TableT:
        """Construct a table where each column has an associated style.

        :param columns: A list of (Column, ColumnStyle) pairs, where the
            ColumnStyle is the style for the column and does **not** have a
            pattern set (or the pattern is set to exactly the column name).
            The ColumnStyle may also be None.
        :param styles: An optional list of extra column styles that will be
            appended to the table's list of styles.
        :param **kwargs: Other parameters to the Table constructor.
        :return: A Table.
        """
        extra_styles = styles if styles else []
        new_columns, new_styles = _style_columns(columns)
        return cls(columns=new_columns, styles=new_styles + extra_styles, **kwargs)

    def to_json_data(self) -> Dict[str, Any]:
        return union(
            [
                self.panel.to_json_data(),
                {
                    "columns": self.columns,
                    "datasource": self.dataSource,
                    "fontSize": self.fontSize,
                    "hideTimeOverride": self.hideTimeOverride,
                    "minSpan": self.minSpan,
                    "pageSize": self.pageSize,
                    "repeat": self.repeat,
                    "scroll": self.scroll,
                    "showHeader": self.showHeader,
                    "sort": self.sort,
                    "styles": self.styles,
                    "targets": self.targets,
                    "timeFrom": self.timeFrom,
                    "transform": self.transform,
                },
            ]
        )
