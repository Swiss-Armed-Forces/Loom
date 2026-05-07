from typing import Callable, TypeVar

import numpy as np
from numpy import array, linspace
from scipy.signal import argrelextrema  # type: ignore[import-untyped]
from sklearn.neighbors import KernelDensity  # type: ignore[import-untyped]

T = TypeVar("T")


def kde_filter_highest_cluster(
    items: list[T],
    get_score: Callable[[T], float],
) -> list[T]:
    """Splits values into clusters using KDE and returns only the highest-value cluster.

    Assumes that higher values represent better or more relevant items.

    The function estimates the density of the value distribution, identifies
    local minima (cluster boundaries), and keeps only the values above the
    last minimum—i.e., the rightmost / highest-scoring cluster.

    Returns: the items of the highest-score cluster; if no clusters are found,
    the original items are returned.
    """
    if len(items) < 1:
        return items

    sorted_items = sorted(items, key=get_score)

    # fit kernel density
    reshaped_scores = array([get_score(t) for t in sorted_items]).reshape(-1, 1)
    kde = KernelDensity(bandwidth="silverman").fit(reshaped_scores)

    # we span a linspace from [min, max], which we can then sample.
    # to generate the linspace we oversample a bit on purpose.
    linspace_samples = linspace(
        get_score(sorted_items[0]),
        get_score(sorted_items[-1]),
        len(sorted_items) * 4,  # oversampling
    ).reshape(-1, 1)

    densities = kde.score_samples(linspace_samples)
    minimas = argrelextrema(densities, np.less)[0]

    if len(minimas) < 1:
        return items

    # keep everything after the last valley -> highest-score cluster
    last_minima = minimas[-1]
    last_minima_value = linspace_samples[last_minima][0]
    filtered_items = [t for t in items if get_score(t) > last_minima_value]

    return filtered_items
