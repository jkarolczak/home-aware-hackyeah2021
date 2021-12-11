import pandas as pd
import numpy as np

from typing import Dict

def clip(x, mini, maxi):
    return max(min(x, maxi), mini)

def norm(x, mini, maxi):
    return clip(x, mini, maxi) / maxi

def partial_utilities(params: Dict, variant: Dict) -> Dict:
    return dict(
        airport=norm(variant['airports'], 0, 10000),
        between_20_30=norm(variant['between_20_30'], 0, 50),
        bus_stop=norm(variant['bus_stop'], 0, 1000),
        car_collisions=norm(variant['car_collisions'], 0, 5),
        civil_services=norm(variant['civil_services'], 0, 1000),
        cr3=variant['cr3']/100,
        crimes=norm(variant['crimes'], 0, 5),
        consumer_expenses=norm(variant['consumer_expenses'], 0, 250000),
        culture_entertainment=norm(variant['culture_entertainment'], 0, 3000),
        health=norm(variant['health'], 0, 1000),
        dating_apps=clip(variant['dating_apps']/100 * 20, 0, 1),
        education=norm(variant['education'], 0, 5),
        freeways=norm(variant['freeways'], 0, 3000),
        garages=norm(variant['garages'], 0, 1000),
        geoscore=variant['geoscore']/100,
        mall=norm(variant['mall'], 0, 3000),
        nature=norm(variant['nature'], 0, 1000),
        over_60=norm(variant['over_60'], 0, 50),
        parcel_lockers=norm(variant['parcel_lockers'], 0, 1000),
        post_office=norm(variant['post_office'], 0, 1000),
        railway_station=norm(variant['railway_station'], 0, 3000),
        railway_tracks=norm(variant['railway_tracks'], 0, 1000),
        sport=variant['sport']/100,
        tram_stop=norm(variant['tram_stop'], 0, 1000),
        university=norm(variant['university'], 0, 5000),
        worship=norm(variant['worship'], 0, 3000)
    )


def global_utility(params: dict, variant: dict):
    U = partial_utilities(params, variant)
    return np.sum(list(U.values()))/np.sum(list(params.values()))


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
