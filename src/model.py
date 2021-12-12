import pandas as pd
import numpy as np

from typing import Dict


default_thresholds = dict(
    airport=10,
    between_20_30=50,
    bus_stop=1,
    car_collisions=5,
    civil_services=1,
    cr3=100,
    crimes=5,
    consumer_expenses=250000,
    culture_entertainment=3,
    health=1,
    dating_apps=10,
    education=5,
    freeways=3,
    garages=0.5,
    geoscore=100,
    mall=3,
    nature=40,
    over_60=50,
    parcel_lockers=1,
    post_office=1,
    railway_station=3,
    railway_tracks=1,
    sport=100,
    tram_stop=1,
    university=5,
    worship=3
)


def clip(x, mini, maxi):
    return max(min(x, maxi), mini)

def norm(x, mini, maxi):
    if maxi == 0: return 0
    return clip(x, mini, maxi) / maxi

def partial_utilities(thresh: Dict, variant: Dict) -> Dict:
    return dict(
        between_20_30=norm(variant['between_20_30'], 0, thresh['between_20_30']),
        bus_stop=norm(variant['bus_stop']/1000, 0, thresh['bus_stop']),
        car_collisions=norm(variant['car_collisions'], 0, thresh['car_collisions']),
        cr3=variant['cr3']/100,
        crimes=norm(variant['crimes'], 0, thresh['crimes']),
        consumer_expenses=norm(variant['consumer_expenses'], 0, thresh['consumer_expenses']),
        culture_entertainment=norm(variant['culture_entertainment']/1000, 0, thresh['culture_entertainment']),
        health=norm(variant['health']/1000, 0, thresh['health']),
        dating_apps=clip(variant['dating_apps']/100 * 20, 0, thresh['dating_apps']),
        education=norm(variant['education'], 0, thresh['education']),
        garages=norm(variant['garages'], 0, thresh['garages']),
        geoscore=variant['geoscore']/100,
        mall=norm(variant['mall']/1000, 0, thresh['mall']),
        nature=norm(variant['nature'], 0, thresh['nature']),
        over_60=norm(variant['over_60'], 0, thresh['over_60']),
        parcel_lockers=norm(variant['parcel_lockers']/1000, 0, thresh['nature']),
        post_office=norm(variant['post_office']/1000, 0, thresh['post_office']),
        railway_station=norm(variant['railway_station']/1000, 0, thresh['railway_station']),
        civil_services=-norm(variant['civil_services']/1000, 0, thresh['civil_services']),
        railway_tracks=-norm(variant['railway_tracks']/1000, 0, thresh['railway_tracks']),
        freeways=-norm(variant['freeways']/1000, 0, thresh['freeways']),
        airport=-norm(variant['airports']/1000, 0, thresh['airport']),
        sport=variant['sport']/100,
        tram_stop=norm(variant['tram_stop']/1000, 0, thresh['tram_stop']),
        university=norm(variant['university']/1000, 0, thresh['university']),
        worship=norm(variant['worship']/1000, 0, thresh['worship'])
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
