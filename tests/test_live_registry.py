import pytest
from unittest.mock import patch, MagicMock

from backend.live import LiveRegistry


@pytest.fixture
def registry():
    return LiveRegistry()


def test_get_root_keys(registry):
    roots = registry.get_root_keys()
    assert "HKEY_LOCAL_MACHINE" in roots
    assert isinstance(roots, list)


def test_parse_invalid_root(registry):
    result = registry.get_subkeys("INVALID_ROOT\\Test")
    assert result == []


def test_parse_empty_path(registry):
    result = registry.get_subkeys("")
    assert result == []


@patch("backend.live.winreg.OpenKey")
@patch("backend.live.winreg.QueryInfoKey")
@patch("backend.live.winreg.EnumKey")
def test_get_subkeys_success(mock_enum, mock_query, mock_open, registry):
    mock_key = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_key
    mock_query.return_value = (2, 0, 0)
    mock_enum.side_effect = ["Sub1", "Sub2"]

    result = registry.get_subkeys("HKEY_LOCAL_MACHINE\\Software")

    assert result == ["Sub1", "Sub2"]


@patch("backend.live.winreg.OpenKey")
@patch("backend.live.winreg.QueryInfoKey")
@patch("backend.live.winreg.EnumKey")
def test_get_subkeys_race_condition(mock_enum, mock_query, mock_open, registry):
    mock_key = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_key
    mock_query.return_value = (2, 0, 0)

    mock_enum.side_effect = ["Sub1", OSError()]

    result = registry.get_subkeys("HKEY_LOCAL_MACHINE\\Software")

    assert result == ["Sub1"]


@patch("backend.live.winreg.OpenKey", side_effect=OSError())
def test_get_subkeys_open_error(mock_open, registry):
    result = registry.get_subkeys("HKEY_LOCAL_MACHINE\\Software")
    assert result == []


@patch("backend.live.winreg.OpenKey")
@patch("backend.live.winreg.QueryInfoKey")
@patch("backend.live.winreg.EnumValue")
def test_get_values_success(mock_enum, mock_query, mock_open, registry):
    mock_key = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_key
    mock_query.return_value = (0, 2, 0)

    mock_enum.side_effect = [
        ("Name1", "Value1", 1),
        ("Name2", 123, 4),
    ]

    result = registry.get_values("HKEY_LOCAL_MACHINE\\Software")

    assert result == [
        ("Name1", registry._type_to_str(1), "Value1"),
        ("Name2", registry._type_to_str(4), "123"),
    ]


@patch("backend.live.winreg.OpenKey")
@patch("backend.live.winreg.QueryInfoKey")
@patch("backend.live.winreg.EnumValue")
def test_get_values_race_condition(mock_enum, mock_query, mock_open, registry):
    mock_key = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_key
    mock_query.return_value = (0, 2, 0)

    mock_enum.side_effect = [
        ("Name1", "Value1", 1),
        OSError(),
    ]

    result = registry.get_values("HKEY_LOCAL_MACHINE\\Software")

    assert result == [
        ("Name1", registry._type_to_str(1), "Value1"),
    ]


@patch("backend.live.winreg.OpenKey", side_effect=OSError())
def test_get_values_open_error(mock_open, registry):
    result = registry.get_values("HKEY_LOCAL_MACHINE\\Software")
    assert result == []


def test_type_to_str_known(registry):
    assert registry._type_to_str(1) == "REG_SZ"


def test_type_to_str_unknown(registry):
    assert registry._type_to_str(99999) == "UNKNOWN"


def test_close_method(registry):
    # Метод должен существовать и не выбрасывать исключений
    registry.close()