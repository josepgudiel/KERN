"""
Secure session serialization utilities.
Replaces unsafe pickle with JSON + Parquet.
"""

import json
import base64
from io import BytesIO
from typing import Any, Dict

import pandas as pd


def serialize_session(data: Dict[str, Any]) -> bytes:
    """
    Serialize session data to JSON bytes.

    DataFrames are converted to Parquet and base64-encoded within JSON.
    Sets are converted to lists. Other values must be JSON-serializable.

    Args:
        data: Dictionary containing session data (may include DataFrames)

    Returns:
        JSON-encoded bytes safe for Redis storage

    Raises:
        ValueError: If data contains non-serializable types
    """
    serialized = {}

    for key, value in data.items():
        if isinstance(value, pd.DataFrame):
            buffer = BytesIO()
            value.to_parquet(buffer, index=True)
            buffer.seek(0)
            serialized[key] = {
                "__type__": "DataFrame",
                "__data__": base64.b64encode(buffer.read()).decode("utf-8"),
            }
        elif isinstance(value, set):
            serialized[key] = {"__type__": "set", "__data__": list(value)}
        elif isinstance(value, (str, int, float, bool, type(None), list, dict)):
            serialized[key] = value
        else:
            raise ValueError(
                f"Cannot serialize session key '{key}': "
                f"type {type(value).__name__} is not supported. "
                f"Use str, int, float, bool, None, list, dict, set, or pd.DataFrame."
            )

    return json.dumps(serialized).encode("utf-8")


def deserialize_session(data: bytes) -> Dict[str, Any]:
    """
    Deserialize session data from JSON bytes.

    Reconstructs DataFrames from Parquet and sets from lists.

    Args:
        data: JSON-encoded bytes from Redis

    Returns:
        Dictionary containing original session data with DataFrames/sets restored

    Raises:
        json.JSONDecodeError: If data is not valid JSON
        ValueError: If Parquet data is corrupted
    """
    serialized = json.loads(data.decode("utf-8"))

    deserialized = {}

    for key, value in serialized.items():
        if isinstance(value, dict) and "__type__" in value:
            if value["__type__"] == "DataFrame":
                parquet_bytes = base64.b64decode(value["__data__"])
                buffer = BytesIO(parquet_bytes)
                deserialized[key] = pd.read_parquet(buffer)
            elif value["__type__"] == "set":
                deserialized[key] = set(value["__data__"])
            else:
                deserialized[key] = value
        else:
            deserialized[key] = value

    return deserialized
