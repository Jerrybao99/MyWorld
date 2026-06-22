GROWTH_REVENUE_THRESHOLDS = {
    (9, 10): lambda v: v > 40,
    (7, 8):  lambda v: 25 <= v <= 40,
    (5, 6):  lambda v: 15 <= v < 25,
    (3, 4):  lambda v: 5 <= v < 15,
    (1, 2):  lambda v: v < 5,
}

GROWTH_PROFIT_THRESHOLDS = {
    (9, 10): lambda v: v > 50,
    (7, 8):  lambda v: 30 <= v <= 50,
    (5, 6):  lambda v: 15 <= v < 30,
    (3, 4):  lambda v: 0 <= v < 15,
    (1, 2):  lambda v: v < 0,
}

STABILITY_DEBT_THRESHOLDS = {
    (9, 10): lambda v: v < 40,
    (7, 8):  lambda v: 40 <= v <= 60,
    (5, 6):  lambda v: 60 < v <= 75,
    (3, 4):  lambda v: 75 < v <= 85,
    (1, 2):  lambda v: v > 85,
}

STABILITY_LIQUIDITY_THRESHOLDS = {
    (9, 10): lambda v: v > 2.5,
    (7, 8):  lambda v: 1.5 <= v <= 2.5,
    (5, 6):  lambda v: 1.0 <= v < 1.5,
    (3, 4):  lambda v: 0.5 <= v < 1.0,
    (1, 2):  lambda v: v < 0.5,
}

RETURN_ROE_THRESHOLDS = {
    (9, 10): lambda v: v > 20,
    (7, 8):  lambda v: 15 <= v <= 20,
    (5, 6):  lambda v: 10 <= v < 15,
    (3, 4):  lambda v: 6 <= v < 10,
    (1, 2):  lambda v: v < 6,
}

RATING_MAP = [
    (8.5, 10.0, "皇冠明珠"),
    (7.0, 8.4,  "优秀白马"),
    (5.5, 6.9,  "鸡肋/观察"),
    (0.0, 5.4,  "垃圾"),
]


def score_metric(value, thresholds):
    import math
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    for (lo, hi), condition in thresholds.items():
        if condition(value):
            return (lo + hi) / 2
    return None
