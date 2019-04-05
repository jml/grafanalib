"""Low-level functions for building Grafana dashboards.

The functions in this module don't enforce Weaveworks policy, and only mildly
encourage it by way of some defaults. Rather, they are ways of building
arbitrary Grafana JSON.
"""

import enum
import itertools
import math
import warnings
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import attr
from typing_extensions import Protocol

# For when we don't actually know what type Grafana wants for a particular field.
Unknown = Any

# Grafana uses "10s" and so forth as markers of time duration.
Duration = str


# A color expressed as a hex code (e.g. #rrggbb)
Color = str


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
    links: List[Unknown] = attr.Factory(list)  # TODO: What type are links?
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


class LegendSort(Enum):
    MIN = "min"
    MAX = "max"
    AVG = "avg"
    CURRENT = "current"
    TOTAL = "total"


@attr.s(frozen=True)
class Legend:
    avg: bool = False
    current: bool = False
    max: bool = False
    min: bool = False
    show: bool = True
    total: bool = False
    values: Optional[bool] = None
    alignAsTable: bool = False
    hideEmpty: bool = False
    hideZero: bool = False
    rightSide: bool = False
    sideWidth: Optional[float] = None
    sort: Optional[LegendSort] = None
    sortDesc: bool = False

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


class BaseTarget:
    """Parent class for targets.

    We have multiple target types, none of which expose anything that we can
    use for structural subtyping. Thus, we'll use nominative subtyping to help
    prevent folk accidentally putting a non-Target in the target slot.
    """


@attr.s(auto_attribs=True, frozen=True)
class Target(BaseTarget):
    """
    Metric to show.

    :param target: Graphite way to select data
    """

    expr: str = ""
    format: TargetFormat = TargetFormat.TIME_SERIES
    legendFormat: str = ""
    interval: str = ""
    intervalFactor: int = 2
    metric: str = ""
    refId: str = ""
    step: int = DEFAULT_STEP
    target: str = ""
    instant: bool = False
    datasource: str = ""

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


@attr.s(auto_attribs=True, frozen=True)
class Tooltip:

    msResolution: bool = True
    shared: bool = True
    sort: int = 0  # TODO: Either 0, 1, or 2, but don't know what these mean.
    valueType: TooltipValueType = TooltipValueType.CUMULATIVE

    def to_json_data(self):
        return {
            "msResolution": self.msResolution,
            "shared": self.shared,
            "sort": self.sort,
            "value_type": self.valueType,
        }


class XAxisMode(Enum):
    TIME = "TIME"
    SERIES = "SERIES"


@attr.s(auto_attribs=True, frozen=True)
class XAxis:

    mode: XAxisMode = XAxisMode.TIME
    name: Optional[str] = None
    values: List[Unknown] = attr.Factory(list)
    show: bool = True

    def to_json_data(self):
        return {"show": self.show}


@attr.s(auto_attribs=True, frozen=True)
class YAxis:
    """A single Y axis.

    Grafana graphs have two Y axes: one on the left and one on the right.
    """

    decimals: Optional[int] = None
    format: Optional[NumberFormat] = None
    label: Optional[str] = None
    logBase: int = 1
    max: Optional[float] = None
    min: Optional[float] = 0
    show: bool = True

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


@attr.s(auto_attribs=True, frozen=True)
class YAxes:
    """The pair of Y axes on a Grafana graph.

    Each graph has two Y Axes, a left one and a right one.
    """

    left: YAxis = YAxis(format=NumberFormat.SHORT)
    right: YAxis = YAxis(format=NumberFormat.SHORT)

    def to_json_data(self):
        return [self.left, self.right]


def single_y_axis(**kwargs) -> YAxes:
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

    @property
    def panel(self) -> Panel:
        ...


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
    panels: Sequence[HasPanel] = attr.Factory(list)
    collapse: bool = False
    editable: bool = True
    height: Pixels = DEFAULT_ROW_HEIGHT
    showTitle: Optional[bool] = None
    title: Optional[str] = None
    repeat: Optional[Unknown] = None  # TODO: What type is this?

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


@attr.s(auto_attribs=True, frozen=True)
class Annotations:
    _list: List[Unknown] = attr.Factory(list)

    def to_json_data(self):
        return {"list": self._list}


@attr.s(auto_attribs=True, frozen=True)
class DataSourceInput:
    pluginId: str
    pluginName: str

    def to_json_data(self) -> Dict[str, Any]:
        return {"pluginId": self.pluginId, "pluginName": self.pluginName, "type": "datasource"}


@attr.s(auto_attribs=True, frozen=True)
class ConstantInput:
    value: Any

    def to_json_data(self) -> Dict[str, Any]:
        return {"type": "constant", "value": self.value}


@attr.s(auto_attribs=True, frozen=True)
class Input:
    name: str
    label: str
    input: Union[DataSourceInput, ConstantInput]
    description: str = ""

    def to_json_data(self) -> Dict[str, Any]:
        return union(
            [
                {"name": self.name, "label": self.label, "description": self.description},
                self.input.to_json_data(),
            ]
        )


@attr.s(auto_attribs=True, frozen=True)
class DashboardLink:
    dashboard: Unknown
    uri: str
    keepTime: bool = True
    title: Optional[str] = None
    type = PanelType.DASHBOARD  # XXX: Is this the right type?

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


@attr.s(auto_attribs=True, frozen=True)
class ExternalLink:
    """ExternalLink creates a top-level link attached to a dashboard.

        :param url: the URL to link to
        :param title: the text of the link
        :param keepTime: if true, the URL params for the dashboard's
            current time period are appended
    """

    uri: str
    title: str
    keepTime: bool = False

    def to_json_data(self):
        return {"keepTime": self.keepTime, "title": self.title, "type": "link", "url": self.uri}


class TemplateType(Enum):
    QUERY = "query"
    INTERVAL = "interval"
    DATASOURCE = "datasource"
    CUSTOM = "custom"
    CONSTANT = "constant"
    ADHOC = "adhoc"


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

    name: str
    query: str
    default: Optional[Any] = None
    dataSource: Optional[str] = None
    label: Optional[str] = None
    allValue: Optional[str] = None
    includeAll: bool = False
    multi: bool = False
    regex: Optional[str] = None
    useTags: bool = False
    tagsQuery: Optional[str] = None
    tagValuesQuery: Optional[str] = None
    refresh: Refresh = Refresh.ON_DASHBOARD_LOAD
    type: TemplateType = TemplateType.QUERY
    hide: TemplateHide = TemplateHide.SHOW

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


@attr.s(auto_attribs=True, frozen=True)
class Templating:
    _list: List[Unknown] = attr.Factory(list)

    def to_json_data(self):
        return {"list": self._list}


@attr.s(auto_attribs=True, frozen=True)
class Time:
    start: str
    end: str

    def to_json_data(self):
        return {"from": self.start, "to": self.end}


DEFAULT_TIME = Time("now-1h", "now")


@attr.s(auto_attribs=True, frozen=True)
class TimePicker:
    refreshIntervals: List[str]
    timeOptions: List[str]

    def to_json_data(self):
        return {"refresh_intervals": self.refreshIntervals, "time_options": self.timeOptions}


DEFAULT_TIME_PICKER = TimePicker(
    refreshIntervals=["5s", "10s", "30s", "1m", "5m", "15m", "30m", "1h", "2h", "1d"],
    timeOptions=["5m", "15m", "1h", "6h", "12h", "24h", "2d", "7d", "30d"],
)


@attr.s(auto_attribs=True, frozen=True)
class Evaluator:
    type: EvaluatorType
    params: List[float]

    def to_json_data(self):
        return {"type": self.type, "params": self.params}


def GreaterThan(value: float) -> Evaluator:
    return Evaluator(EvaluatorType.GT, [value])


def LowerThan(value: float) -> Evaluator:
    return Evaluator(EvaluatorType.LT, [value])


def WithinRange(from_value: float, to_value: float) -> Evaluator:
    return Evaluator(EvaluatorType.WITHIN_RANGE, [from_value, to_value])


def OutsideRange(from_value: float, to_value: float) -> Evaluator:
    return Evaluator(EvaluatorType.OUTSIDE_RANGE, [from_value, to_value])


def NoValue() -> Evaluator:
    return Evaluator(EvaluatorType.NO_VALUE, [])


@attr.s(auto_attribs=True, frozen=True)
class TimeRange:
    """A time range for an alert condition.

    A condition has to hold for this length of time before triggering.

    :param str from_time: Either a number + unit (s: second, m: minute,
        h: hour, etc)  e.g. ``"5m"`` for 5 minutes, or ``"now"``.
    :param str to_time: Either a number + unit (s: second, m: minute,
        h: hour, etc)  e.g. ``"5m"`` for 5 minutes, or ``"now"``.
    """

    from_time: str
    to_time: str

    def to_json_data(self):
        return [self.from_time, self.to_time]


@attr.s(auto_attribs=True, frozen=True)
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

    target: Target
    evaluator: Evaluator
    timeRange: TimeRange
    operator: Operator
    reducerType: ReducerType
    type: ConditionType = ConditionType.QUERY

    def to_json_data(self):
        queryParams = [self.target.refId, self.timeRange.from_time, self.timeRange.to_time]
        return {
            "evaluator": self.evaluator,
            "operator": {"type": self.operator},
            "query": {"model": self.target, "params": queryParams},
            "reducer": {"params": [], "type": self.reducerType},
            "type": self.type,
        }


@attr.s(auto_attribs=True, frozen=True)
class Alert:

    name: str
    message: str
    alertConditions: List[AlertCondition]
    executionErrorState: AlertRuleState = AlertRuleState.ALERTING
    frequency: Duration = "60s"
    handler: int = 1  # XXX: Not sure what this means.
    noDataState: AlertRuleState = AlertRuleState.NO_DATA
    notifications: List[Unknown] = attr.Factory(list)

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


@attr.s(auto_attribs=True, frozen=True)
class Dashboard:

    title: str
    rows: List[Row]
    annotations: Annotations = Annotations()
    editable: bool = True
    gnetId: Optional[int] = None
    hideControls: bool = False
    id: Optional[int] = None
    inputs: List[Unknown] = attr.Factory(list)
    links: List[Unknown] = attr.Factory(list)
    refresh: Duration = DEFAULT_REFRESH
    schemaVersion: int = SCHEMA_VERSION
    sharedCrosshair: bool = False
    style: DashboardStyle = DashboardStyle.DARK
    tags: List[str] = attr.Factory(list)
    templating: Templating = Templating()
    time: Time = DEFAULT_TIME
    timePicker: TimePicker = DEFAULT_TIME_PICKER
    timezone: str = UTC
    version: int = 0
    uid: Optional[str] = None

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


@attr.s(auto_attribs=True, frozen=True)
class Graph:
    """
    Generates Graph panel json structure.

    :param dataSource: DataSource's name
    :param minSpan: Minimum width for each panel
    :param repeat: Template's name to repeat Graph on
    """

    panel: Panel
    targets: Sequence[BaseTarget]
    aliasColors: Dict[str, Color] = attr.Factory(dict)
    bars: bool = False
    dataSource: Optional[str] = None
    error: bool = False
    fill: int = 1
    grid: Grid = Grid()
    isNew: bool = True
    legend: Legend = Legend()
    lines: bool = True
    lineWidth: int = DEFAULT_LINE_WIDTH
    nullPointMode: NullPointMode = NullPointMode.CONNECTED
    percentage: bool = False
    pointRadius: int = DEFAULT_POINT_RADIUS
    points: bool = False
    renderer: Renderer = DEFAULT_RENDERER
    repeat: Optional[Unknown] = None
    seriesOverrides: List[Unknown] = attr.Factory(list)
    stack: bool = False
    steppedLine: bool = False
    timeFrom: Optional[Unknown] = None
    timeShift: Optional[Unknown] = None
    tooltip: Tooltip = Tooltip()
    xAxis: XAxis = XAxis()
    yAxes: YAxes = YAxes()
    alert: Optional[Unknown] = None

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


@attr.s(auto_attribs=True, frozen=True)
class SparkLine:
    fillColor: RGBA = BLUE_RGBA
    full: bool = False
    lineColor: RGB = BLUE_RGB
    show: bool = False

    def to_json_data(self):
        return {
            "fillColor": self.fillColor,
            "full": self.full,
            "lineColor": self.lineColor,
            "show": self.show,
        }


@attr.s(auto_attribs=True, frozen=True)
class ValueMap:
    op: str
    text: str
    value: str

    def to_json_data(self):
        return {"op": self.op, "text": self.text, "value": self.value}


@attr.s(auto_attribs=True, frozen=True)
class RangeMap:
    start: str
    end: str
    text: str

    def to_json_data(self):
        return {"from": self.start, "to": self.end, "text": self.text}


@attr.s(auto_attribs=True, frozen=True)
class Gauge:

    minValue: int = 0
    maxValue: int = 100
    show: bool = False
    thresholdLabels: bool = False
    thresholdMarkers: bool = True

    def to_json_data(self):
        return {
            "maxValue": self.maxValue,
            "minValue": self.minValue,
            "show": self.show,
            "thresholdLabels": self.thresholdLabels,
            "thresholdMarkers": self.thresholdMarkers,
        }


@attr.s(auto_attribs=True, frozen=True)
class Text:
    """Generates a Text panel."""

    type = PanelType.TEXT

    panel: Panel
    content: str
    error: bool = False
    mode: TextMode = TextMode.MARKDOWN

    def to_json_data(self):
        return union(
            [
                self.panel.to_json_data(),
                {"content": self.content, "error": self.error, "mode": self.mode},
            ]
        )


@attr.s(auto_attribs=True, frozen=True)
class AlertList:
    """Generates the AlertList Panel."""

    type = PanelType.ALERTLIST

    panel: Panel
    limit: int = DEFAULT_LIMIT
    onlyAlertsOnDashboard: bool = True
    show: AlertListShow = AlertListShow.CURRENT
    sortOrder: SortOrder = SortOrder.ASC
    stateFilter: List[Unknown] = attr.Factory(list)

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


@attr.s(auto_attribs=True, frozen=True)
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
    panel: Panel

    dataSource: str
    targets: Sequence[BaseTarget]
    cacheTimeout: Optional[Duration] = None
    colors: Tuple[RGBA, RGBA, RGBA] = (GREEN, ORANGE, RED)
    colorBackground: bool = False
    colorValue: bool = False
    decimals: Optional[int] = None
    format: NumberFormat = NumberFormat.NO
    gauge: Gauge = Gauge()
    hideTimeOverride: bool = False
    interval: Optional[Unknown] = None
    mappingType: MappingType = MappingType.VALUE_TO_TEXT
    mappingTypes: List[Mapping] = attr.Factory(
        lambda: [MAPPING_VALUE_TO_TEXT, MAPPING_RANGE_TO_TEXT]
    )
    maxDataPoints: int = 100
    nullText: Optional[str] = None
    nullPointMode: NullPointMode = NullPointMode.CONNECTED
    postfix: str = ""
    postfixFontSize: Percent = Percent(50)
    prefix: str = ""
    prefixFontSize: Percent = Percent(50)
    rangeMaps: List[RangeMap] = attr.Factory(list)
    repeat: Optional[Unknown] = None
    sparkline: SparkLine = SparkLine()
    thresholds: str = ""
    valueFontSize: Percent = Percent(80)
    valueName: ValueType = DEFAULT_VALUE_TYPE
    valueMaps: List[ValueMap] = attr.Factory(list)
    timeFrom: Optional[Duration] = None

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


@attr.s(auto_attribs=True, frozen=True)
class DateColumnStyleType:
    TYPE = "date"

    dateFormat: str = "YYYY-MM-DD HH:mm:ss"

    def to_json_data(self):
        return {"dateFormat": self.dateFormat, "type": self.TYPE}


@attr.s(auto_attribs=True, frozen=True)
class NumberColumnStyleType:
    TYPE = "number"

    colorMode: Optional[Unknown] = None
    colors: Tuple[RGBA, RGBA, RGBA] = (GREEN, ORANGE, RED)
    thresholds: List[float] = attr.Factory(list)
    decimals: int = 2
    unit: NumberFormat = NumberFormat.SHORT

    def to_json_data(self):
        return {
            "colorMode": self.colorMode,
            "colors": self.colors,
            "decimals": self.decimals,
            "thresholds": self.thresholds,
            "type": self.TYPE,
            "unit": self.unit,
        }


@attr.s(auto_attribs=True, frozen=True)
class StringColumnStyleType:
    TYPE = "string"

    preserveFormat: bool
    sanitize: bool

    def to_json_data(self):
        return {"preserveFormat": self.preserveFormat, "sanitize": self.sanitize, "type": self.TYPE}


@attr.s(auto_attribs=True, frozen=True)
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


@attr.s(auto_attribs=True, frozen=True)
class ColumnSort:
    col: Optional[Unknown] = None
    desc: bool = False

    def to_json_data(self):
        return {"col": self.col, "desc": self.desc}


@attr.s(auto_attribs=True, frozen=True)
class Column:
    """Details of an aggregation column in a table panel.

    :param text: name of column
    :param value: aggregation function
    """

    text: str = "Avg"
    value: str = "avg"  # TODO: This should probably be an enum

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


@attr.s(auto_attribs=True, frozen=True)
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

    panel: Panel
    dataSource: str
    targets: Sequence[BaseTarget]
    columns: List[Column] = attr.Factory(list)
    fontSize: Percent = Percent(100)
    hideTimeOverride: bool = False
    pageSize: Optional[int] = None
    repeat: Optional[Unknown] = None
    scroll: bool = True
    showHeader: bool = True
    sort: ColumnSort = ColumnSort()
    styles: List[ColumnStyle] = attr.Factory(
        lambda: [
            ColumnStyle(alias="Time", pattern="time", type=DateColumnStyleType()),
            ColumnStyle(pattern="/.*/"),
        ]
    )
    timeFrom: Optional[Duration] = None
    transform: Transform = Transform.COLUMNS

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
