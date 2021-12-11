import pandas as pd
import numpy as np


def clip(x, mini, maxi):
    return max(min(x, maxi), mini)


def partial_utilities(params: dict, variant: dict):
    return dict(
        dating_apps=variant['dating_apps_percent']/100,
        university=variant['university_distance'],
        education=variant['education_distance'],
    )


def global_utility(params: dict, variant: dict):
    U = partial_utilities(params, variant)
    return np.sum(list(U.values()))


if __name__ == '__main__':
    p1 = dict(
        dating_apps_weight=0.3,
        university_weight=0.7,
        university_scale=1000, # meters
    )
    v1 = dict(
        dating_apps_percent=70,
        university_distance=500,
    )
    print('params =', p1)
    print('variant =', v1)
    print('u =', partial_utilities(p1, v1))
    print('U =', global_utility(p1, v1))
