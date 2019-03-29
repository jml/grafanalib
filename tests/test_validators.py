import attr
import grafanalib.validators as validators
import pytest


def create_attribute():
    return attr.Attribute(
        name="x", default=None, validator=None, repr=True, cmp=True, hash=True, init=True
    )


@pytest.mark.parametrize("item", ("24h", "7d", "1M", "+24h", "-24h", "60s", "2m"))
def test_is_interval(item):
    assert validators.is_interval(None, create_attribute(), item) is None


def test_is_interval_raises():
    with pytest.raises(ValueError):
        validators.is_interval(None, create_attribute(), "1")


@pytest.mark.parametrize("color", ("#111111", "#ffffff"))
def test_is_color_code(color):
    assert validators.is_color_code(None, create_attribute(), color) is None


@pytest.mark.parametrize("color", ("111111", "#gggggg", "#1111111", "#11111"))
def test_is_color_code_raises(color):
    with pytest.raises(ValueError):
        validators.is_color_code(None, create_attribute(), color)


def test_list_of():
    etype = int
    check = (1, 2, 3)
    val = validators.is_list_of(etype)
    res = val(None, create_attribute(), check)
    assert res is None


def test_list_of_raises():
    etype = int
    check = "a"
    with pytest.raises(ValueError):
        val = validators.is_list_of(etype)
        val(None, create_attribute(), check)
