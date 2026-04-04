"""Demo data generators — copied from app.py (no Streamlit dependencies)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _generate_demo_df() -> pd.DataFrame:
    """Generate a realistic coffee-shop demo with timestamps, 2 locations, 18 products."""
    rng = np.random.default_rng(42)

    products_data = [
        ("Espresso",            3.50, 0.13, 0.28),
        ("Americano",           4.00, 0.11, 0.30),
        ("Latte",               5.50, 0.16, 0.35),
        ("Cappuccino",          5.00, 0.12, 0.35),
        ("Cold Brew",           5.50, 0.07, 0.38),
        ("Flat White",          5.50, 0.05, 0.35),
        ("Macchiato",           4.50, 0.04, 0.33),
        ("Mocha",               6.00, 0.04, 0.40),
        ("Hot Chocolate",       4.50, 0.03, 0.38),
        ("Green Tea",           3.50, 0.02, 0.28),
        ("Croissant",           3.50, 0.07, 0.45),
        ("Blueberry Muffin",    3.00, 0.05, 0.42),
        ("Avocado Toast",       9.00, 0.03, 0.52),
        ("Granola Bowl",        7.50, 0.02, 0.48),
        ("BLT Sandwich",        8.50, 0.02, 0.55),
        ("Cheesecake Slice",    6.00, 0.01, 0.40),
        ("Brownie",             3.50, 0.015, 0.38),
        ("Bagel & Cream Cheese",5.00, 0.015, 0.45),
    ]
    names     = [p[0] for p in products_data]
    prices    = np.array([p[1] for p in products_data])
    weights   = np.array([p[2] for p in products_data])
    cost_pcts = np.array([p[3] for p in products_data])
    weights = weights / weights.sum()

    locations   = ["Main Street", "Downtown"]
    loc_weights = [0.60, 0.40]

    n = 1400
    end   = pd.Timestamp.today().normalize()
    start = end - pd.DateOffset(months=6)

    total_days = (end - start).days
    rand_days  = rng.integers(0, total_days + 1, size=n)
    hours      = rng.integers(7, 21, size=n)
    minutes    = rng.integers(0, 60, size=n)

    timestamps = [
        start + pd.Timedelta(days=int(d), hours=int(h), minutes=int(m))
        for d, h, m in zip(rand_days, hours, minutes)
    ]

    pidx   = rng.choice(len(names), size=n, p=weights)
    lidx   = rng.choice(len(locations), size=n, p=loc_weights)
    qtys   = rng.integers(1, 4, size=n)
    jitter = 1 + rng.uniform(-0.05, 0.05, size=n)

    order_ids = []
    order_counter = 1
    i = 0
    while i < n:
        roll = rng.random()
        if roll < 0.60:
            size = 1
        elif roll < 0.90:
            size = 2
        else:
            size = 3
        size = min(size, n - i)
        order_id = f"ORD-{order_counter:04d}"
        order_ids.extend([order_id] * size)
        order_counter += 1
        i += size

    rows = [
        {
            "order_id":   order_ids[i],
            "product":    names[pidx[i]],
            "quantity":   int(qtys[i]),
            "unit_price": round(float(prices[pidx[i]] * jitter[i]), 2),
            "revenue":    round(float(prices[pidx[i]] * jitter[i] * qtys[i]), 2),
            "cost":       round(float(prices[pidx[i]] * cost_pcts[pidx[i]] * qtys[i]), 2),
            "date":       timestamps[i],
            "location":   locations[lidx[i]],
        }
        for i in range(n)
    ]

    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def _generate_retail_demo_df() -> pd.DataFrame:
    """Generate a realistic retail-store demo with timestamps, 1 location, 20 products."""
    rng = np.random.default_rng(99)

    products_data = [
        ("Classic T-Shirt",       24.99, 0.12, 0.45),
        ("Denim Jeans",           59.99, 0.09, 0.50),
        ("Running Sneakers",      89.99, 0.06, 0.52),
        ("Canvas Tote Bag",       19.99, 0.08, 0.40),
        ("Scented Candle",        14.99, 0.07, 0.35),
        ("Ceramic Mug",           12.99, 0.06, 0.38),
        ("Notebook Set (3-pack)", 9.99,  0.05, 0.42),
        ("Stainless Water Bottle",29.99, 0.05, 0.48),
        ("Sunglasses",            34.99, 0.04, 0.44),
        ("Phone Case",            15.99, 0.06, 0.32),
        ("Baseball Cap",          19.99, 0.05, 0.40),
        ("Wool Scarf",            29.99, 0.03, 0.46),
        ("Leather Wallet",        39.99, 0.04, 0.50),
        ("Desk Lamp",             44.99, 0.03, 0.55),
        ("Yoga Mat",              34.99, 0.03, 0.48),
        ("Bluetooth Speaker",     49.99, 0.03, 0.55),
        ("Lip Balm (3-pack)",     7.99,  0.04, 0.30),
        ("Hand Cream",            11.99, 0.03, 0.35),
        ("Greeting Cards (5-pk)", 8.99,  0.02, 0.28),
        ("Keychain",              6.99,  0.02, 0.25),
    ]
    names     = [p[0] for p in products_data]
    prices    = np.array([p[1] for p in products_data])
    weights   = np.array([p[2] for p in products_data])
    cost_pcts = np.array([p[3] for p in products_data])
    weights = weights / weights.sum()

    location = "Main Street"

    n = 1200
    end   = pd.Timestamp.today().normalize()
    start = end - pd.DateOffset(months=6)

    total_days = (end - start).days
    rand_days  = rng.integers(0, total_days + 1, size=n)
    hours      = rng.integers(9, 20, size=n)
    minutes    = rng.integers(0, 60, size=n)

    timestamps = [
        start + pd.Timedelta(days=int(d), hours=int(h), minutes=int(m))
        for d, h, m in zip(rand_days, hours, minutes)
    ]

    pidx   = rng.choice(len(names), size=n, p=weights)
    qtys   = rng.integers(1, 3, size=n)
    jitter = 1 + rng.uniform(-0.03, 0.03, size=n)

    order_ids: list[str] = []
    order_counter = 1
    i = 0
    while i < n:
        roll = rng.random()
        if roll < 0.55:
            size = 1
        elif roll < 0.90:
            size = 2
        else:
            size = 3
        size = min(size, n - i)
        order_id = f"RET-{order_counter:04d}"
        order_ids.extend([order_id] * size)
        order_counter += 1
        i += size

    rows = [
        {
            "order_id":   order_ids[i],
            "product":    names[pidx[i]],
            "quantity":   int(qtys[i]),
            "unit_price": round(float(prices[pidx[i]] * jitter[i]), 2),
            "revenue":    round(float(prices[pidx[i]] * jitter[i] * qtys[i]), 2),
            "cost":       round(float(prices[pidx[i]] * cost_pcts[pidx[i]] * qtys[i]), 2),
            "date":       timestamps[i],
            "location":   location,
        }
        for i in range(n)
    ]

    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
