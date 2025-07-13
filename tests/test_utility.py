from datetime import datetime

import pytest

from backend.core.utility import json_serializer


def test_json_serializer_with_datetime():
    dt = datetime(2025, 7, 13, 14, 30, 0)
    result = json_serializer(dt)
    assert result == "2025-07-13T14:30:00"

def test_json_serializer_with_wrong_type():
    with pytest.raises(TypeError) as excinfo:
        json_serializer(123)
    assert "not serializable" in str(excinfo.value)
