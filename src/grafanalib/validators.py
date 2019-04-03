import re

import attr


def is_interval(_instance, _attribute, value):
    """
    A validator that raises a :exc:`ValueError` if the attribute value is not
    matching regular expression.
    """
    if not re.match(r"^[+-]?\d*[smhdMY]$", value):
        raise ValueError(
            "valid interval should be a string "
            "matching an expression: ^[+-]?\\d*[smhdMY]$. "
            "Examples: 24h 7d 1M +24h -24h"
        )


def is_color_code(_instance, attribute, value):
    """
    A validator that raises a :exc:`ValueError` if attribute value
    is not valid color code.
    Value considered as valid color code if it starts with # char
    followed by hexadecimal.
    """
    err = "{attr} should be a valid color code".format(attr=attribute.name)
    if not value.startswith("#"):
        raise ValueError(err)
    if len(value) != 7:
        raise ValueError(err)
    try:
        int(value[1:], 16)
    except ValueError:
        raise ValueError(err)


@attr.attributes(repr=False, slots=True, frozen=True)
class _ListOfValidator:
    etype = attr.attr()

    def __call__(self, inst, attribute, value):
        if False in set(map(lambda el: isinstance(el, self.etype), value)):
            raise ValueError(
                "{attr} should be list of {etype}".format(attr=attribute.name, etype=self.etype)
            )

    def __repr__(self):
        return "<is value is the list of {etype}>".format(etype=self.etype)


def is_list_of(etype):
    """
    A validator that raises a :exc:`ValueError` if the attribute value is not
    in a provided list.

    :param choices: List of valid choices
    """
    return _ListOfValidator(etype)
