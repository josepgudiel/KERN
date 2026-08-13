"""Demo data generators — copied from app.py (no Streamlit dependencies).

── Why this file has structure in it ──────────────────────────────────────────
The recommendation engine (engine/recommendations.py) only fires when a pattern
clears four gates: statistical significance, trend acceleration, being an
outlier within the dataset, and a dollar impact over the minimum. That is
deliberate — it is what stops the product inventing advice from noise.

The demo therefore cannot be noise. An earlier version of this generator drew
every product from a fixed weight and a fixed price with ±5% jitter, which is
pure noise by construction: no product had a significant trend, no product had
measurable elasticity, and no two products were bought together more than
chance. The engine correctly found nothing, so the Action Center rendered its
empty state and the demo showed a customer nothing at all.

The generator below plants four findable stories in the data. None of them
bypasses a gate — each one is a real pattern that the engine discovers on its
own, exactly as it would in a customer's export:

  1. Drip Coffee   — the volume item, genuinely underpriced, price-tested
                     across four levels with a mild demand response
                     (elasticity ≈ -0.5, so raising the price is safe).
  2. Flat White    — a real decline that steepens over the six months.
  3. Cold Brew     — a real rise that steepens over the six months.
  4. Latte + Croissant — a genuine co-purchase habit, well above chance.

Everything else stays flat and noisy, which is what makes those four stand out
as outliers rather than as the loudest of eighteen equally busy signals.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# ── Coffee-shop demo ─────────────────────────────────────────────────────────

# Drip Coffee's price test. Four levels the shop ran over the six months; the
# quantity mix shifts with each one, which is what gives the engine a real
# elasticity to measure instead of jitter. The spread and the tightness of the
# quantity mix are both load-bearing: elasticity is measured per transaction,
# so a narrow price range or a wide quantity spread buries the signal under
# integer noise and the regression never reaches significance.
_DRIP_PRICE_LEVELS = (1.75, 2.15, 2.60, 3.00)
_DRIP_QTY3_SHARE   = (0.88, 0.62, 0.34, 0.10)  # P(bought 3) at each price
_DRIP_QTY1_SHARE   = 0.03                      # a few singles, at every price

# Co-purchase habits, as (product A, product B, share of orders).
#
# Three of them, not one, and that is forced by the engine rather than by
# taste. A bundle rec has to be an *outlier* among the qualifying pairs, and
# relative_standing() reports no outlier at all when given fewer than three
# values. Three is still not enough: the largest z-score attainable from n
# values is sqrt(n-1), so n=3 caps out at 1.41 and can never clear the 1.5
# threshold, while n=4 reaches 1.73 and can. Each pair yields two directional
# rules, so three pairs leave headroom above that floor. The pair members are
# also kept scarce outside their pair, so both directions of each rule clear
# apriori's confidence floor instead of only one.
# Shape of the two trends. The exponent makes the curve convex so the second
# half moves faster than the first (compute_trend checks for exactly that); the
# floor stops the declining product decaying to nothing, because a product that
# ends at zero has no recent revenue left to clear the dollar-impact gate.
_DOWN_AMP, _DOWN_EXP, _DOWN_FLOOR = 0.85, 2.2, 0.17
_UP_AMP, _UP_EXP = 3.0, 2.6

# Share of line items held by the three products that carry a story.
_W_DRIP, _W_FLATWHITE, _W_COLDBREW, _W_LATTE = 0.390, 0.150, 0.055, 0.145
_N_ORDERS = 2600

_PAIRS = (
    ("Latte",     "Croissant",        0.172),
    ("Mocha",     "Brownie",          0.055),
    ("Macchiato", "Cheesecake Slice", 0.050),
)


def _generate_demo_df() -> pd.DataFrame:
    """Generate a realistic coffee-shop demo with timestamps, 2 locations, 19 products.

    Returns roughly 2,800 line items over six months. See the module docstring
    for the four patterns planted in it and why they are there.
    """
    rng = np.random.default_rng(42)

    # (name, base_price, base_weight, cost_pct, trend)
    #   flat  — steady all period (the background the outliers stand against)
    #   down  — accelerating decline      up — accelerating rise
    #   test  — Drip Coffee's price experiment
    products_data = [
        ("Drip Coffee",         2.40, _W_DRIP, 0.22, "test"),
        ("Latte",               5.50, _W_LATTE, 0.35, "flat"),
        ("Espresso",            3.50, 0.100, 0.28, "flat"),
        ("Americano",           4.00, 0.085, 0.30, "flat"),
        ("Cappuccino",          5.00, 0.085, 0.35, "flat"),
        ("Croissant",           3.50, 0.050, 0.45, "flat"),
        ("Cold Brew",           5.50, _W_COLDBREW, 0.38, "up"),
        ("Flat White",          5.50, _W_FLATWHITE, 0.35, "down"),
        ("Macchiato",           4.50, 0.012, 0.33, "flat"),
        ("Mocha",               6.00, 0.012, 0.40, "flat"),
        ("Blueberry Muffin",    3.00, 0.035, 0.42, "flat"),
        ("Hot Chocolate",       4.50, 0.025, 0.38, "flat"),
        ("Green Tea",           3.50, 0.020, 0.28, "flat"),
        ("Avocado Toast",       9.00, 0.010, 0.52, "flat"),
        ("Granola Bowl",        7.50, 0.008, 0.48, "flat"),
        ("BLT Sandwich",        8.50, 0.008, 0.55, "flat"),
        ("Cheesecake Slice",    6.00, 0.008, 0.40, "flat"),
        ("Brownie",             3.50, 0.008, 0.38, "flat"),
        ("Bagel & Cream Cheese",5.00, 0.011, 0.45, "flat"),
    ]

    names      = [p[0] for p in products_data]
    base_price = {p[0]: p[1] for p in products_data}
    cost_pct   = {p[0]: p[3] for p in products_data}
    trend      = {p[0]: p[4] for p in products_data}
    base_w     = np.array([p[2] for p in products_data], dtype=float)
    base_w    /= base_w.sum()

    locations   = ["Main Street", "Downtown"]
    loc_weights = [0.60, 0.40]

    end   = pd.Timestamp.today().normalize()
    start = end - pd.DateOffset(months=6)
    total_days = (end - start).days

    # Friday and Saturday carry the week — this is what the staffing page reads.
    dow_mult = np.array([0.82, 0.85, 0.95, 1.05, 1.35, 1.30, 0.78])

    def profile(kind: str, t: float) -> float:
        """Demand multiplier for a product at progress `t` in [0, 1].

        The exponent is what makes a trend *accelerate*: the curve is convex, so
        the second half moves faster than the first. compute_trend() checks for
        exactly that, and a straight line would not pass it.
        """
        if kind == "down":
            return float(max(_DOWN_FLOOR, 1.0 - _DOWN_AMP * t ** _DOWN_EXP))
        if kind == "up":
            return float(1.0 + _UP_AMP * t ** _UP_EXP)
        return 1.0

    def drip_level(t: float) -> int:
        """Which of the four price-test levels was live at progress `t`."""
        return min(int(t * len(_DRIP_PRICE_LEVELS)), len(_DRIP_PRICE_LEVELS) - 1)

    # ── Build orders ─────────────────────────────────────────────────────────
    n_orders = _N_ORDERS
    rows: list[dict] = []

    for order_no in range(1, n_orders + 1):
        day = int(rng.integers(0, total_days + 1))
        ts = start + pd.Timedelta(
            days=day, hours=int(rng.integers(7, 21)), minutes=int(rng.integers(0, 60))
        )
        # Busy days get more orders: re-roll a quiet day some of the time.
        if rng.random() > dow_mult[ts.dayofweek] / dow_mult.max():
            day = int(rng.integers(0, total_days + 1))
            ts = start + pd.Timedelta(
                days=day, hours=int(rng.integers(7, 21)), minutes=int(rng.integers(0, 60))
            )

        t = day / total_days if total_days else 0.0
        location = locations[int(rng.choice(len(locations), p=loc_weights))]

        w = base_w * np.array([profile(trend[n], t) for n in names])
        w /= w.sum()

        roll_pair = rng.random()
        cutoff = 0.0
        items: list[str] = []
        for a, b, rate in _PAIRS:
            cutoff += rate
            if roll_pair < cutoff:
                items = [a, b]
                break
        if not items:
            roll = rng.random()
            size = 1 if roll < 0.55 else (2 if roll < 0.87 else 3)
            items = list(rng.choice(names, size=size, replace=False, p=w))

        for product in items:
            if trend[product] == "test":
                lvl = drip_level(t)
                unit_price = _DRIP_PRICE_LEVELS[lvl] * (1 + rng.uniform(-0.008, 0.008))
                qty = 3 if rng.random() < _DRIP_QTY3_SHARE[lvl] else 2
                if rng.random() < _DRIP_QTY1_SHARE:
                    qty = 1
            else:
                unit_price = base_price[product] * (1 + rng.uniform(-0.05, 0.05))
                qty = int(rng.integers(1, 4))

            unit_price = round(float(unit_price), 2)
            rows.append({
                "order_id":   f"ORD-{order_no:04d}",
                "product":    product,
                "quantity":   qty,
                "unit_price": unit_price,
                "revenue":    round(unit_price * qty, 2),
                "cost":       round(base_price[product] * cost_pct[product] * qty, 2),
                "date":       ts,
                "location":   location,
            })

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
