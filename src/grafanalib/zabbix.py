from typing import List, Optional, Tuple

import attr
from attr.validators import in_, instance_of
from grafanalib.core import (
    BLANK,
    DEFAULT_ROW_HEIGHT,
    GREEN,
    RGBA,
    DashboardLink,
    Enum,
    Percent,
    Pixels,
)
from grafanalib.validators import is_color_code, is_interval, is_list_of

ZABBIX_TRIGGERS_TYPE = "alexanderzobnin-zabbix-triggers-panel"


class ZabbixMode(Enum):
    METRICS = 0
    SERVICES = 1
    TEXT = 2


ZABBIX_SLA_PROP_STATUS = {"name": "Status", "property": "status"}

ZABBIX_SLA_PROP_SLA = {"name": "SLA", "property": "sla"}

ZABBIX_SLA_PROP_OKTIME = {"name": "OK time", "property": "okTime"}

ZABBIX_SLA_PROP_PROBTIME = {"name": "Problem time", "property": "problemTime"}

ZABBIX_SLA_PROP_DOWNTIME = {"name": "Down time", "property": "downtimeTime"}

ZABBIX_EVENT_PROBLEMS = {"text": "Problems", "value": [1]}

ZABBIX_EVENT_OK = {"text": "OK", "value": [0]}

ZABBIX_EVENT_ALL = {"text": "All", "value": [0, 1]}

ZABBIX_TRIGGERS_SHOW_ALL = "all triggers"
ZABBIX_TRIGGERS_SHOW_ACK = "acknowledged"
ZABBIX_TRIGGERS_SHOW_NACK = "unacknowledged"

ZABBIX_SORT_TRIGGERS_BY_CHANGE = {"text": "last change", "value": "lastchange"}
ZABBIX_SORT_TRIGGERS_BY_SEVERITY = {"text": "severity", "value": "priority"}


@attr.s(frozen=True)
class ZabbixTargetOptions:
    showDisabledItems = attr.ib(default=False, validator=instance_of(bool))

    def to_json_data(self):
        return {"showDisabledItems": self.showDisabledItems}


@attr.s(frozen=True)
class ZabbixTargetField:
    filter = attr.ib(default="", validator=instance_of(str))

    def to_json_data(self):
        return {"filter": self.filter}


@attr.s(frozen=True)
class ZabbixTarget:
    """Generates Zabbix datasource target JSON structure.

    Grafana-Zabbix is a plugin for Grafana allowing
    to visualize monitoring data from Zabbix and create
    dashboards for analyzing metrics and realtime monitoring.

    Grafana docs on using Zabbix pluging: http://docs.grafana-zabbix.org/

    :param application: zabbix application name
    :param expr: zabbix arbitary query
    :param functions: list of zabbix aggregation functions
    :param group: zabbix host group
    :param host: hostname
    :param intervalFactor: defines interval between metric queries
    :param item: regexp that defines which metric to query
    :param itService: zabbix it service name
    :param mode: query mode type
    :param options: additional query options
    :param refId: target reference id
    :param slaProperty: zabbix it service sla property.
        Zabbix returns the following availability information about IT service
        Status - current status of the IT service
        SLA - SLA for the given time interval
        OK time - time the service was in OK state, in seconds
        Problem time - time the service was in problem state, in seconds
        Down time - time the service was in scheduled downtime, in seconds
    :param textFilter: query text filter. Use regex to extract a part of
        the returned value.
    :param useCaptureGroups: defines if capture groups should be used during
        metric query
    """

    application = attr.ib(default="", validator=instance_of(str))
    expr = attr.ib(default="")
    functions = attr.ib(default=attr.Factory(list))
    group = attr.ib(default="", validator=instance_of(str))
    host = attr.ib(default="", validator=instance_of(str))
    intervalFactor = attr.ib(default=2, validator=instance_of(int))
    item = attr.ib(default="", validator=instance_of(str))
    itService = attr.ib(default="", validator=instance_of(str))
    mode = attr.ib(default=ZabbixMode.METRICS, validator=instance_of(ZabbixMode))
    options = attr.ib(
        default=attr.Factory(ZabbixTargetOptions), validator=instance_of(ZabbixTargetOptions)
    )
    refId = attr.ib(default="")
    slaProperty = attr.ib(default=attr.Factory(dict))
    textFilter = attr.ib(default="", validator=instance_of(str))
    useCaptureGroups = attr.ib(default=False, validator=instance_of(bool))

    def to_json_data(self):
        obj = {
            "application": ZabbixTargetField(self.application),
            "expr": self.expr,
            "functions": self.functions,
            "group": ZabbixTargetField(self.group),
            "host": ZabbixTargetField(self.host),
            "intervalFactor": self.intervalFactor,
            "item": ZabbixTargetField(self.item),
            "mode": self.mode,
            "options": self.options,
            "refId": self.refId,
        }
        if self.mode == ZabbixMode.SERVICES:
            obj["slaProperty"] = (self.slaProperty,)
            obj["itservice"] = {"name": self.itService}
        if self.mode == ZabbixMode.TEXT:
            obj["textFilter"] = self.textFilter
            obj["useCaptureGroups"] = self.useCaptureGroups
        return obj


class ZabbixFunction:
    """Base type for Zabbix functions."""


@attr.s(frozen=True)
class ZabbixDeltaFunction(ZabbixFunction):
    """ZabbixDeltaFunction

    Convert absolute values to delta, for example, bits to bits/sec
    http://docs.grafana-zabbix.org/reference/functions/#delta
    """

    added = attr.ib(default=False, validator=instance_of(bool))

    def to_json_data(self):
        text = "delta()"
        definition = {"category": "Transform", "name": "delta", "defaultParams": [], "params": []}
        return {"added": self.added, "text": text, "def": definition, "params": []}


@attr.s(frozen=True)
class ZabbixGroupByFunction(ZabbixFunction):
    """ZabbixGroupByFunction

    Takes each timeseries and consolidate its points falled in given interval
    into one point using function, which can be one of: avg, min, max, median.
    http://docs.grafana-zabbix.org/reference/functions/#groupBy
    """

    _options = ("avg", "min", "max", "median")
    _default_interval = "1m"
    _default_function = "avg"

    added = attr.ib(default=False, validator=instance_of(bool))
    interval = attr.ib(default=_default_interval, validator=is_interval)
    function = attr.ib(default=_default_function, validator=in_(_options))

    def to_json_data(self):
        text = "groupBy({interval}, {function})"
        definition = {
            "category": "Transform",
            "name": "groupBy",
            "defaultParams": [self._default_interval, self._default_function],
            "params": [
                {"name": "interval", "type": "string"},
                {"name": "function", "options": self._options, "type": "string"},
            ],
        }
        return {
            "def": definition,
            "text": text.format(interval=self.interval, function=self.function),
            "params": [self.interval, self.function],
            "added": self.added,
        }


@attr.s(auto_attribs=True, frozen=True)
class ZabbixScaleFunction(ZabbixFunction):
    """ZabbixScaleFunction

    Takes timeseries and multiplies each point by the given factor.
    http://docs.grafana-zabbix.org/reference/functions/#scale
    """

    _default_factor = 100

    added: bool = False
    factor: float = _default_factor

    def to_json_data(self):
        text = "scale({factor})"
        definition = {
            "category": "Transform",
            "name": "scale",
            "defaultParams": [self._default_factor],
            "params": [{"name": "factor", "options": [100, 0.01, 10, -1], "type": "float"}],
        }
        return {
            "def": definition,
            "text": text.format(factor=self.factor),
            "params": [self.factor],
            "added": self.added,
        }


@attr.s(frozen=True)
class ZabbixAggregateByFunction(ZabbixFunction):
    """ZabbixAggregateByFunction

    Takes all timeseries and consolidate all its points falled in given
    interval into one point using function, which can be one of:
        avg, min, max, median.
    http://docs.grafana-zabbix.org/reference/functions/#aggregateBy
    """

    _options = ("avg", "min", "max", "median")
    _default_interval = "1m"
    _default_function = "avg"

    added = attr.ib(default=False, validator=instance_of(bool))
    interval = attr.ib(default=_default_interval, validator=is_interval)
    function = attr.ib(default=_default_function, validator=in_(_options))

    def to_json_data(self):
        text = "aggregateBy({interval}, {function})"
        definition = {
            "category": "Aggregate",
            "name": "aggregateBy",
            "defaultParams": [self._default_interval, self._default_function],
            "params": [
                {"name": "interval", "type": "string"},
                {"name": "function", "options": self._options, "type": "string"},
            ],
        }
        return {
            "def": definition,
            "text": text.format(interval=self.interval, function=self.function),
            "params": [self.interval, self.function],
            "added": self.added,
        }


@attr.s(frozen=True)
class ZabbixAverageFunction(ZabbixFunction):
    """ZabbixAverageFunction

    Deprecated, use aggregateBy(interval, avg) instead.
    http://docs.grafana-zabbix.org/reference/functions/#average
    """

    _default_interval = "1m"

    added = attr.ib(default=False, validator=instance_of(bool))
    interval = attr.ib(default=_default_interval, validator=is_interval)

    def to_json_data(self):
        text = "average({interval})"
        definition = {
            "category": "Aggregate",
            "name": "average",
            "defaultParams": [self._default_interval],
            "params": [{"name": "interval", "type": "string"}],
        }
        return {
            "def": definition,
            "text": text.format(interval=self.interval),
            "params": [self.interval],
            "added": self.added,
        }


@attr.s(frozen=True)
class ZabbixMaxFunction(ZabbixFunction):
    """ZabbixMaxFunction

    Deprecated, use aggregateBy(interval, max) instead.
    http://docs.grafana-zabbix.org/reference/functions/#max
    """

    _default_interval = "1m"

    added = attr.ib(default=False, validator=instance_of(bool))
    interval = attr.ib(default=_default_interval, validator=is_interval)

    def to_json_data(self):
        text = "max({interval})"
        definition = {
            "category": "Aggregate",
            "name": "max",
            "defaultParams": [self._default_interval],
            "params": [{"name": "interval", "type": "string"}],
        }
        return {
            "def": definition,
            "text": text.format(interval=self.interval),
            "params": [self.interval],
            "added": self.added,
        }


@attr.s(frozen=True)
class ZabbixMedianFunction(ZabbixFunction):
    """ZabbixMedianFunction

    Deprecated, use aggregateBy(interval, median) instead.
    http://docs.grafana-zabbix.org/reference/functions/#median
    """

    _default_interval = "1m"

    added = attr.ib(default=False, validator=instance_of(bool))
    interval = attr.ib(default="1m", validator=is_interval)

    def to_json_data(self):
        text = "median({interval})"
        definition = {
            "category": "Aggregate",
            "name": "median",
            "defaultParams": [self._default_interval],
            "params": [{"name": "interval", "type": "string"}],
        }
        return {
            "def": definition,
            "text": text.format(interval=self.interval),
            "params": [self.interval],
            "added": self.added,
        }


@attr.s(frozen=True)
class ZabbixMinFunction(ZabbixFunction):
    """ZabbixMinFunction

    Deprecated, use aggregateBy(interval, min) instead.
    http://docs.grafana-zabbix.org/reference/functions/#min
    """

    _default_interval = "1m"

    added = attr.ib(default=False, validator=instance_of(bool))
    interval = attr.ib(default=_default_interval, validator=is_interval)

    def to_json_data(self):
        text = "min({interval})"
        definition = {
            "category": "Aggregate",
            "name": "min",
            "defaultParams": [self._default_interval],
            "params": [{"name": "interval", "type": "string"}],
        }
        return {
            "def": definition,
            "text": text.format(interval=self.interval),
            "params": [self.interval],
            "added": self.added,
        }


@attr.s(frozen=True)
class ZabbixSumSeriesFunction(ZabbixFunction):
    """ZabbixSumSeriesFunction

    This will add metrics together and return the sum at each datapoint.
    This method required interpolation of each timeseries so it may
    cause high CPU load.
    Try to combine it with groupBy() function to reduce load.
    http://docs.grafana-zabbix.org/reference/functions/#sumSeries
    """

    added = attr.ib(default=False)

    def to_json_data(self):
        text = "sumSeries()"
        definition = {
            "category": "Aggregate",
            "name": "sumSeries",
            "defaultParams": [],
            "params": [],
        }
        return {"added": self.added, "text": text, "def": definition, "params": []}


@attr.s(frozen=True)
class ZabbixBottomFunction(ZabbixFunction):

    _options = ("avg", "min", "max", "median")
    _default_number = 5
    _default_function = "avg"

    added = attr.ib(default=False, validator=instance_of(bool))
    number = attr.ib(default=_default_number, validator=instance_of(int))
    function = attr.ib(default=_default_function, validator=in_(_options))

    def to_json_data(self):
        text = "bottom({number}, {function})"
        definition = {
            "category": "Filter",
            "name": "bottom",
            "defaultParams": [self._default_number, self._default_function],
            "params": [
                {"name": "number", "type": "string"},
                {"name": "function", "options": self._options, "type": "string"},
            ],
        }
        return {
            "def": definition,
            "text": text.format(number=self.number, function=self.function),
            "params": [self.number, self.function],
            "added": self.added,
        }


@attr.s(frozen=True)
class ZabbixTopFunction(ZabbixFunction):

    _options = ("avg", "min", "max", "median")
    _default_number = 5
    _default_function = "avg"

    added = attr.ib(default=False, validator=instance_of(bool))
    number = attr.ib(default=_default_number, validator=instance_of(int))
    function = attr.ib(default=_default_function, validator=in_(_options))

    def to_json_data(self):
        text = "top({number}, {function})"
        definition = {
            "category": "Filter",
            "name": "top",
            "defaultParams": [self._default_number, self._default_function],
            "params": [
                {"name": "number", "type": "string"},
                {"name": "function", "options": self._options, "type": "string"},
            ],
        }
        return {
            "def": definition,
            "text": text.format(number=self.number, function=self.function),
            "params": [self.number, self.function],
            "added": self.added,
        }


@attr.s(frozen=True)
class ZabbixTrendValueFunction(ZabbixFunction):
    """ZabbixTrendValueFunction

    Specifying type of trend value returned by Zabbix when
    trends are used (avg, min or max).
    http://docs.grafana-zabbix.org/reference/functions/#trendValue
    """

    _options = ("avg", "min", "max")
    _default_type = "avg"
    added = attr.ib(default=False, validator=instance_of(bool))
    type = attr.ib(default=_default_type, validator=in_(_options))

    def to_json_data(self):
        text = "trendValue({type})"
        definition = {
            "category": "Trends",
            "name": "trendValue",
            "defaultParams": [self._default_type],
            "params": [{"name": "type", "options": self._options, "type": "string"}],
        }
        return {
            "def": definition,
            "text": text.format(type=self.type),
            "params": [self.type],
            "added": self.added,
        }


@attr.s(frozen=True)
class ZabbixTimeShiftFunction(ZabbixFunction):
    """ZabbixTimeShiftFunction

    Draws the selected metrics shifted in time.
    If no sign is given, a minus sign ( - ) is implied which will
    shift the metric back in time.
    If a plus sign ( + ) is given, the metric will be shifted forward in time.
    http://docs.grafana-zabbix.org/reference/functions/#timeShift
    """

    _options = ("24h", "7d", "1M", "+24h", "-24h")
    _default_interval = "24h"

    added = attr.ib(default=False, validator=instance_of(bool))
    interval = attr.ib(default=_default_interval)

    def to_json_data(self):
        text = "timeShift({interval})"
        definition = {
            "category": "Time",
            "name": "timeShift",
            "defaultParams": [self._default_interval],
            "params": [{"name": "interval", "options": self._options, "type": "string"}],
        }
        return {
            "def": definition,
            "text": text.format(interval=self.interval),
            "params": [self.interval],
            "added": self.added,
        }


@attr.s(frozen=True)
class ZabbixSetAliasFunction(ZabbixFunction):
    """ZabbixSetAliasFunction

    Returns given alias instead of the metric name.
    http://docs.grafana-zabbix.org/reference/functions/#setAlias
    """

    alias = attr.ib(validator=instance_of(str))
    added = attr.ib(default=False, validator=instance_of(bool))

    def to_json_data(self):
        text = "setAlias({alias})"
        definition = {
            "category": "Alias",
            "name": "setAlias",
            "defaultParams": [],
            "params": [{"name": "alias", "type": "string"}],
        }
        return {
            "def": definition,
            "text": text.format(alias=self.alias),
            "params": [self.alias],
            "added": self.added,
        }


@attr.s(frozen=True)
class ZabbixSetAliasByRegexFunction(ZabbixFunction):
    """ZabbixSetAliasByRegexFunction

    Returns part of the metric name matched by regex.
    http://docs.grafana-zabbix.org/reference/functions/#setAliasByRegex
    """

    regexp = attr.ib(validator=instance_of(str))
    added = attr.ib(default=False, validator=instance_of(bool))

    def to_json_data(self):
        text = "setAliasByRegex({regexp})"
        definition = {
            "category": "Alias",
            "name": "setAliasByRegex",
            "defaultParams": [],
            "params": [{"name": "aliasByRegex", "type": "string"}],
        }
        return {
            "def": definition,
            "text": text.format(regexp=self.regexp),
            "params": [self.regexp],
            "added": self.added,
        }


def zabbixMetricTarget(
    application: str,
    group: str,
    host: str,
    item: str,
    functions: Optional[List[ZabbixFunction]] = None,
) -> ZabbixTarget:
    functions = functions if functions else []
    return ZabbixTarget(
        mode=ZabbixMode.METRICS,
        application=application,
        group=group,
        host=host,
        item=item,
        functions=functions,
    )


def zabbixServiceTarget(service, sla=None):
    if sla is None:
        sla = ZABBIX_SLA_PROP_STATUS
    return ZabbixTarget(mode=ZabbixMode.SERVICES, itService=service, slaProperty=sla)


def zabbixTextTarget(application, group, host, item, text, useCaptureGroups=False):
    return ZabbixTarget(
        mode=ZabbixMode.TEXT,
        application=application,
        group=group,
        host=host,
        item=item,
        textFilter=text,
        useCaptureGroups=useCaptureGroups,
    )


@attr.s(frozen=True)
class ZabbixColor:
    color = attr.ib(validator=is_color_code)
    priority = attr.ib(validator=instance_of(int))
    severity = attr.ib(validator=instance_of(str))
    show = attr.ib(default=True, validator=instance_of(bool))

    def to_json_data(self):
        return {
            "color": self.color,
            "priority": self.priority,
            "severity": self.severity,
            "show": self.show,
        }


def convertZabbixSeverityColors(colors: List[Tuple[str, str]]) -> List[ZabbixColor]:
    zabbix_colors = []
    for priority, item in enumerate(colors):
        if isinstance(item, ZabbixColor):
            zabbix_colors.append(item)
        else:
            c, s = item
            zabbix_colors.append(ZabbixColor(color=c, priority=priority, severity=s))
    return zabbix_colors


ZABBIX_SEVERITY_COLORS = convertZabbixSeverityColors(
    [
        ("#B7DBAB", "Not classified"),
        ("#82B5D8", "Information"),
        ("#E5AC0E", "Warning"),
        ("#C15C17", "Average"),
        ("#BF1B00", "High"),
        ("#890F02", "Disaster"),
    ]
)


@attr.s(frozen=True)
class ZabbixTrigger:

    application = attr.ib(default="", validator=instance_of(str))
    group = attr.ib(default="", validator=instance_of(str))
    host = attr.ib(default="", validator=instance_of(str))
    trigger = attr.ib(default="", validator=instance_of(str))

    def to_json_data(self):
        return {
            "application": ZabbixTargetField(self.application),
            "group": ZabbixTargetField(self.group),
            "host": ZabbixTargetField(self.host),
            "trigger": ZabbixTargetField(self.trigger),
        }


@attr.s(frozen=True)
class ZabbixTriggersPanel:
    """ZabbixTriggersPanel

    :param dataSource: query datasource name
    :param title: panel title
    :param ackEventColor: acknowledged triggers color
    :param customLastChangeFormat: defines last change field data format.
        See momentjs docs for time format:
        http://momentjs.com/docs/#/displaying/format/
    :param description: additional panel description
    :param fontSize: panel font size
    :param height: panel height in Pixels
    :param hideHostsInMaintenance: defines if triggers form hosts
        in maintenance should be shown
    :param hostField: defines if host field should be shown
    :param hostTechNameField: defines if field with host technical name should
        be shown
    :param id: panel identificator
    :param infoField: defines if field with host info should be shown
    :param lastChangeField: defines if field with last change
        time should be shown
    :param limit: defines number of queried triggers
    :param links: list of dashboard links
    :param markAckEvents: defines if acknowledged triggers should be colored
        with different color
    :param minSpan: defines panel minimum spans
    :param okEventColor: defines color for triggers with Ok status
    :param pageSize: defines number of triggers per panel page
    :param scroll: defines if scroll should be shown
    :param severityField: defines if severity field should be shown
    :param showEvents: defines event type to query (Ok, Problems, All)
    :param showTriggers: defines trigger type to query
        (all, acknowledged, unacknowledged)
    :param sortTriggersBy: defines trigger sort policy
    :param span: defines span number for panel
    :param statusField: defines if status field should be shown
    :param transparent: defines if panel should be transparent
    :param triggerSeverity: defines colors for trigger severity,
    :param triggers: trigger query

    """

    dataSource = attr.ib()
    title = attr.ib()

    ackEventColor = attr.ib(default=attr.Factory(lambda: BLANK), validator=instance_of(RGBA))
    ageField = attr.ib(default=True, validator=instance_of(bool))
    customLastChangeFormat = attr.ib(default=False, validator=instance_of(bool))
    description = attr.ib(default="", validator=instance_of(str))
    fontSize = attr.ib(default=attr.Factory(Percent), validator=instance_of(Percent))
    height = attr.ib(default=DEFAULT_ROW_HEIGHT, validator=instance_of(Pixels))
    hideHostsInMaintenance = attr.ib(default=False, validator=instance_of(bool))
    hostField = attr.ib(default=True, validator=instance_of(bool))
    hostTechNameField = attr.ib(default=False, validator=instance_of(bool))
    id = attr.ib(default=None)
    infoField = attr.ib(default=True, validator=instance_of(bool))
    lastChangeField = attr.ib(default=True, validator=instance_of(bool))

    lastChangeFormat = attr.ib(default="")
    limit = attr.ib(default=10, validator=instance_of(int))
    links = attr.ib(default=attr.Factory(list), validator=is_list_of(DashboardLink))
    markAckEvents = attr.ib(default=False, validator=instance_of(bool))
    minSpan = attr.ib(default=None)
    okEventColor = attr.ib(default=attr.Factory(lambda: GREEN), validator=instance_of(RGBA))
    pageSize = attr.ib(default=10, validator=instance_of(int))
    repeat = attr.ib(default=None)
    scroll = attr.ib(default=True, validator=instance_of(bool))
    severityField = attr.ib(default=False, validator=instance_of(bool))
    showEvents = attr.ib(default=attr.Factory(lambda: ZABBIX_EVENT_PROBLEMS))
    showTriggers = attr.ib(default=ZABBIX_TRIGGERS_SHOW_ALL)
    sortTriggersBy = attr.ib(default=attr.Factory(lambda: ZABBIX_SORT_TRIGGERS_BY_CHANGE))
    span = attr.ib(default=None)
    statusField = attr.ib(default=False, validator=instance_of(bool))
    transparent = attr.ib(default=False, validator=instance_of(bool))
    triggerSeverity = attr.ib(default=ZABBIX_SEVERITY_COLORS, converter=convertZabbixSeverityColors)
    triggers = attr.ib(default=attr.Factory(ZabbixTrigger), validator=instance_of(ZabbixTrigger))

    def to_json_data(self):
        return {
            "type": ZABBIX_TRIGGERS_TYPE,
            "datasource": self.dataSource,
            "title": self.title,
            "ackEventColor": self.ackEventColor,
            "ageField": self.ageField,
            "customLastChangeFormat": self.customLastChangeFormat,
            "description": self.description,
            "fontSize": self.fontSize,
            "height": self.height,
            "hideHostsInMaintenance": self.hideHostsInMaintenance,
            "hostField": self.hostField,
            "hostTechNameField": self.hostTechNameField,
            "id": self.id,
            "infoField": self.infoField,
            "lastChangeField": self.lastChangeField,
            "lastChangeFormat": self.lastChangeFormat,
            "limit": self.limit,
            "links": self.links,
            "markAckEvents": self.markAckEvents,
            "minSpan": self.minSpan,
            "okEventColor": self.okEventColor,
            "pageSize": self.pageSize,
            "repeat": self.repeat,
            "scroll": self.scroll,
            "severityField": self.severityField,
            "showEvents": self.showEvents,
            "showTriggers": self.showTriggers,
            "sortTriggersBy": self.sortTriggersBy,
            "span": self.span,
            "statusField": self.statusField,
            "transparent": self.transparent,
            "triggers": self.triggers,
            "triggerSeverity": self.triggerSeverity,
        }
