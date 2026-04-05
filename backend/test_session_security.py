"""
Test secure session serialization.
Verify that DataFrames and other data survive round-trip serialization.
"""

import pandas as pd
from session_utils import serialize_session, deserialize_session


def test_serialize_dataframe():
    """Test that DataFrames are correctly serialized and deserialized."""
    df = pd.DataFrame({
        "product": ["Coffee", "Tea", "Juice"],
        "sales": [100, 50, 75],
        "price": [5.99, 4.50, 3.25],
    })

    data = {"df": df, "metadata": {"user": "jose", "session_id": "12345"}}
    serialized = serialize_session(data)
    recovered = deserialize_session(serialized)

    assert "df" in recovered
    assert isinstance(recovered["df"], pd.DataFrame)
    assert recovered["df"].shape == df.shape
    assert (recovered["df"]["product"] == df["product"]).all()
    assert (recovered["df"]["sales"] == df["sales"]).all()
    assert (recovered["df"]["price"] == df["price"]).all()
    assert recovered["metadata"] == {"user": "jose", "session_id": "12345"}

    print("PASS: DataFrame serialization")


def test_serialize_primitives():
    """Test serialization of primitive types."""
    data = {
        "string": "hello",
        "int": 42,
        "float": 3.14,
        "bool": True,
        "none": None,
        "list": [1, 2, 3],
        "dict": {"key": "value"},
    }

    serialized = serialize_session(data)
    recovered = deserialize_session(serialized)

    assert recovered["string"] == "hello"
    assert recovered["int"] == 42
    assert recovered["float"] == 3.14
    assert recovered["bool"] is True
    assert recovered["none"] is None
    assert recovered["list"] == [1, 2, 3]
    assert recovered["dict"] == {"key": "value"}

    print("PASS: Primitive types serialization")


def test_serialize_set():
    """Test that sets survive round-trip as sets."""
    data = {"dismissed_recs": {"rec_1", "rec_2", "rec_3"}}
    serialized = serialize_session(data)
    recovered = deserialize_session(serialized)

    assert isinstance(recovered["dismissed_recs"], set)
    assert recovered["dismissed_recs"] == {"rec_1", "rec_2", "rec_3"}

    print("PASS: Set serialization")


def test_full_session_roundtrip():
    """Test a realistic session payload matching main.py usage."""
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=5),
        "product": ["A", "B", "A", "C", "B"],
        "revenue": [100.0, 200.0, 150.0, 50.0, 300.0],
        "quantity": [10, 20, 15, 5, 30],
    })

    data = {
        "df": df,
        "raw_cols": ["date", "product", "revenue", "quantity"],
        "currency": "$",
        "uploaded_at": "2024-01-01T00:00:00",
        "last_accessed": "2024-01-01T00:00:00",
        "dismissed_recs": {"rec_a", "rec_b"},
        "product_clusters": df.head(2),
    }

    serialized = serialize_session(data)
    recovered = deserialize_session(serialized)

    assert isinstance(recovered["df"], pd.DataFrame)
    assert recovered["df"].shape == df.shape
    assert recovered["raw_cols"] == ["date", "product", "revenue", "quantity"]
    assert recovered["currency"] == "$"
    assert isinstance(recovered["dismissed_recs"], set)
    assert recovered["dismissed_recs"] == {"rec_a", "rec_b"}
    assert isinstance(recovered["product_clusters"], pd.DataFrame)

    print("PASS: Full session round-trip")


def test_unsupported_type():
    """Test that unsupported types raise ValueError."""
    data = {"func": lambda x: x}

    try:
        serialize_session(data)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"PASS: Unsupported type correctly rejected: {e}")


def test_no_pickle_in_output():
    """Verify serialized bytes are valid JSON, not pickle."""
    import json

    df = pd.DataFrame({"a": [1, 2, 3]})
    data = {"df": df, "key": "value"}
    serialized = serialize_session(data)

    # Must be valid JSON
    parsed = json.loads(serialized.decode("utf-8"))
    assert isinstance(parsed, dict)
    assert parsed["key"] == "value"
    assert parsed["df"]["__type__"] == "DataFrame"

    print("PASS: Output is JSON, not pickle")


if __name__ == "__main__":
    test_serialize_dataframe()
    test_serialize_primitives()
    test_serialize_set()
    test_full_session_roundtrip()
    test_unsupported_type()
    test_no_pickle_in_output()
    print("\nAll serialization tests passed!")
