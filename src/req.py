import requests
import json
import os
import warnings
import urllib3
import utm

from collections import defaultdict
from deepdiff import DeepHash
from functools import lru_cache
from urllib.parse import urljoin
from typing import Tuple, Dict

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

with open("src/connection.json", "r") as fp:
    _config = json.loads(fp.read())

_cache_debug = False
_cache_dict = defaultdict(dict)
_cache_dir = _config.get("cache_dir", "src/.cache")
if not os.path.exists(_cache_dir):
    os.mkdir(_cache_dir)


def _payload_hash(payload: str) -> str:
    return str(DeepHash(payload)[payload])
    

def _api(endpoint: str, payload: dict, base: str = "https://gateway.oapi.bik.pl/") -> str:
    # if endpoint + payload is cached in a file, read and return it

    payload_str = json.dumps(payload)
    cache_file = os.path.join(_cache_dir, f"{endpoint}=={_payload_hash(payload_str)}.json")
    if _cache_debug: print('CHECK FOR CACHE', cache_file)
    if cache_file in _cache_dict:
        # level 1 cache
        if _cache_debug: print('L1 CACHE', cache_file)
        return _cache_dict[endpoint][payload_str]
    elif os.path.exists(cache_file):
        # level 2 cache
        with open(cache_file, "r") as f:
            for line in f.read().split('\n'):
                if not line: continue
                try:
                    data = json.loads(line)
                except:
                    raise Exception('Error reading JSON: ', line)
                inp, out = data["input"], data["output"]
                if payload == inp:
                    if _cache_debug: print('L2 CACHE', cache_file)
                    _cache_dict[endpoint][payload_str] = out
                    return out

    if _cache_debug: print('FETCH', endpoint)
    response = requests.request("POST", urljoin(base, endpoint),
        headers={
            "BIK-OAPI-Key": _config["BIK-OAPI-Key"],
            "Content-Type": "application/json"
        },
        data=payload_str,
        cert=(_config["cert-crt"], _config["cert-key"]),
        verify=False
    )
    assert response.status_code == 200, f"API Error ({response.status_code}) ¯\_(ツ)_/¯"
    data = response.json()

    _cache_dict[endpoint][payload_str] = data
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    if _cache_debug: print('SAVE CACHE', cache_file)
    with open(cache_file, "a") as f:
        f.write(json.dumps(dict(input=payload, output=data)) + '\n')
    return data


def _api3_safety(address: Dict) -> Dict:
    payload = {
            "address": {
                "code": str(address["code"]),
                "city": address["city"],
                "street": address["street"],
                "building_number": str(address["buildingNumber"]),
            },
            "grid_list": [500],
            "category_list": ["price", "crime", "road_accident"],
    }
    
    return _api("bik-api-3/bezpieczenstwo-adres", payload)[0]["details"]

def _api4_nearest_poi(address: Dict, poi_type: str) -> float:
    payload = {
        "size": "100",
        "address": address,
        "nearestPOI": poi_type
    }
    return _api("bik-api-4/punkty-zainteresowania-adres", payload)["nearestPOI"]


def _api4_number_poi(address: Dict, poi_type: str) -> float:
    payload = {
        "size": "500",
        "address": address,
        "poinumber": poi_type
    }
    return _api("bik-api-4/liczba-poi-adres", payload)["poinumber"]
    
    
def _api4_demographic(address: Dict, demographicData: str) -> float:
    payload = {
        "size": "100",
        "address": address,
        "demographicData": demographicData
    }
    return _api("bik-api-4/dane-demograficzne-adres", payload)["demographicData"]
    
    
def _api6(address: Dict, section: str) -> float:
    payload = {
        "size": "STAT_250M",
        "productCode": "ALL",
        "address": address,
        "section": section
    }
    return _api("bik-api-6/address", payload)["geostats"]    


def _api10_address_point(address: Dict, address_point: str) -> float:
    payload = {
        "size": "100",
        "address": {
            "code": address["code"],
            "city": address["city"],
            "street": address["street"],
            "buildingNumber": address["buildingNumber"]
        },
        "addressPoint": address_point
    }
    return _api("bik-api-10/odleglosc-punkt-adres", payload)["addressPoint"]


def _api10_area_statistic(address: Dict, area_statistic: str) -> float:
    payload = {
        "size": "500",
        "address": {
            "code": address["code"],
            "city": address["city"],
            "street": address["street"],
            "buildingNumber": address["buildingNumber"]
        },
        "areaStatistic": area_statistic
    }
    return _api("bik-api-10/charakterystyka-obszaru-adres", payload)["areaStatistic"]

def _api11(address: Dict, activity: str) -> float:
    address = {
        "code": str(address)[:2] + "-" + str(address)[2:],
        "city": address["city"],
        "street": address["street"],
        "building_number": str(address["buildingNumber"])
    }
    
    payload = {
        "size": "500M",
        "address": address,
        "category": activity
    }
    return float(_api("bik-api-11/zachowania-wg-adresu", payload)["value"][:-1])


def airports(address: Dict) -> float:
    return _api4_nearest_poi(address, "D_TRANSPORT_LOTNISKO_MIEDZYNARODOWE")["D_TRANSPORT_LOTNISKO_MIEDZYNARODOWE"]


def between_20_30(address: Dict) -> float:
    groups = [
        "POPT2024",
        "POPT2529"
    ]
    return sum([_api4_demographic(address, group)[group] for group in groups])


def bus_stop(address: Dict) -> float:
    return _api4_nearest_poi(address, "D_TRANSPORT_PRZYSTANEK_AUTOBUSOWY")["D_TRANSPORT_PRZYSTANEK_AUTOBUSOWY"]


def car_collisions(data: Dict) -> float:
    return data["details"]["hitting_a_pedestrian"]


def civil_services(address: Dict) -> float:
    fire_stations = [
        "D_URZAD_I_SLUZBA_PUBLICZNA_SLUZBY_PUBLICZNE_OCHOTNICZA_STRAZ_POZARNA",
        "D_URZAD_I_SLUZBA_PUBLICZNA_SLUZBY_PUBLICZNE_STRAZ_POZARNA"
    ]
    fire_stations = [_api4_nearest_poi(address, poi)[poi] for poi in fire_stations]
    police = _api4_nearest_poi(address, "D_URZAD_I_SLUZBA_PUBLICZNA_SLUZBY_PUBLICZNE_KOMENDA_POLICJI")["D_URZAD_I_SLUZBA_PUBLICZNA_SLUZBY_PUBLICZNE_KOMENDA_POLICJI"]
    return (min(fire_stations) + police) / 2

    
def coordinates(address: Dict) -> tuple:
    result = _api6(address, "SR_CR3_KREDYTOBIORCY")[0]["inputDataCoordinates"]
    return result["utm_x"], result["utm_y"]


def cr3(address: Dict) -> tuple:
    return float(_api6(address, "SR_CR3_KREDYTOBIORCY")[0]["result"])


def crimes(data: Dict) -> float:
    return sum(data["details"].values())


def consumer_expenses(address: Dict) -> float:
    payload = {
        "size": 100,
        "address": address,
        "wealth": "WK_RAZEM"
    }
    return _api("bik-api-4/zamoznosc-adres", payload)["wealth"]["WK_RAZEM"]


def culture_entertainment(address: Dict) -> float:
    pois = [
        "D_ROZRYWKA_I_KULTURA_KINO",
        "D_ROZRYWKA_I_KULTURA_KREGIELNIE",
        "D_ROZRYWKA_I_KULTURA_MUZEUM",
        "D_ROZRYWKA_I_KULTURA_TEATR"
    ]
    distances = [_api4_nearest_poi(address, poi)[poi] for poi in pois]
    return sum(distances) / len(distances)


def dating_apps(address: Dict) -> float:
    return _api11(address, "PROFILE_DATING")


def education(address: Dict) -> float:
    pois = [
        "EDUKACJA_PRZEDSZKOLA_I_PUNKTY_PRZEDSZKOLNE",
        "EDUKACJA_SZKOLY_PODSTAWOWE",
        "EDUKACJA_LICEA_OGOLNOKSZTALCACE_I_PROFILOWANE",
        "EDUKACJA_ZESPOL_SZKOL",
        "EDUKACJA_TECHNIKA",
        "EDUKACJA_SZKOLY_BRANZOWE",
    ]
    return sum([_api4_number_poi(address, poi)[poi] for poi in pois])


def freeways(address: Dict) -> float:
    autostr = float(_api10_address_point(address, "odl_autost")["odl_autost"])
    ekspres = float(_api10_address_point(address, "odl_drEksp")["odl_drEksp"])
    return min(autostr, ekspres)
    

def garages(address: Dict) -> float:
    return int(_api10_area_statistic(address, "garaze")["garaze"])


def geoscore(address: Dict) -> float:
    return float(_api("bik-api-5/geoscore-adres", address)["score"])


def health(address: Dict) -> float:
    return _api4_nearest_poi(address, "D_ZDROWIE")["D_ZDROWIE"]


def mall(address: Dict) -> float:
    return _api4_nearest_poi(address, "D_CENTRUM_HANDLOWE")["D_CENTRUM_HANDLOWE"]


def nature(address: Dict) -> float:
    lasy = float(_api10_area_statistic(address, "lasy")["lasy"])
    zielen = float(_api10_area_statistic(address, "zielen_mi")["zielen_mi"])
    return sum(lasy, zielen)


def over_60(address: Dict) -> float:
    groups = [
        "POPT6064",
        "POPT6569",
        "POPT7074",
        "POPT7599"
    ]
    return sum([_api4_demographic(address, group)[group] for group in groups])


def parcel_lockers(address: Dict) -> float:
    return _api4_nearest_poi(address, "D_PRZESYLKI_PACZKOMAT")["D_PRZESYLKI_PACZKOMAT"]


def post_office(address: Dict) -> float:
    return _api4_nearest_poi(address, "D_POCZTA")["D_POCZTA"]


def price(data: Dict) -> float:
    return data["details"]["offer_price"]


def price_and_safety(address: Dict) -> Tuple[float, float, float]:
    data = _api3_safety(address)
    return price(data[0]), crimes(data[1]), car_collisions(data[2])


def railway_station(address: Dict) -> float:
    return _api4_nearest_poi(address, "D_TRANSPORT_PKP_PRZYSTANEK_LUB_STACJA_DWORZEC")["D_TRANSPORT_PKP_PRZYSTANEK_LUB_STACJA_DWORZEC"]


def railway_tracks(address: Dict) -> float:
    return float(_api10_address_point(address, "odl_tory")["odl_tory"])


def sport(address: Dict) -> float:
    return _api11(address, "PROFILE_SPORT_ACTIVE")


def tram_stop(address: Dict) -> float:
    return _api4_nearest_poi(address, "D_TRANSPORT_PRZYSTANEK_TRAMWAJOWY")["D_TRANSPORT_PRZYSTANEK_TRAMWAJOWY"]


def university(address: Dict) -> float:
    return _api4_nearest_poi(address, "D_EDUKACJA_WYZSZE_SZKOLY_PUBLICZNE")["D_EDUKACJA_WYZSZE_SZKOLY_PUBLICZNE"]


def worship(address: Dict) -> float:
    return _api4_nearest_poi(address, "D_MIEJSCE_KULTU_KOSCIOL")["D_MIEJSCE_KULTU_KOSCIOL"]


@lru_cache(maxsize=256)
def criterions(code: int, city: str, street: str, buildingNumber: int) -> Dict:
    functions = [
        consumer_expenses, university, education, dating_apps, between_20_30, 
        parcel_lockers, civil_services, railway_tracks, freeways, airports, 
        nature, garages, bus_stop, tram_stop, railway_station, post_office, 
        mall, culture_entertainment, health, geoscore, cr3, over_60, worship, 
        sport, coordinates
    ]
    address = { "code": code, "city": city, "street": street, "buildingNumber": buildingNumber }
    results = {fun.__name__: fun(address) for fun in functions}
    price, crimes, car_collisions = price_and_safety(address)
    results["price"] = price
    results["crimes"] = crimes
    results["car_collisions"] = car_collisions
    a, b = results["coordinates"]
    results["latlon"] = utm.to_latlon(a, b, 34, 'U') # Hardcode Łódź
    return results
    

if __name__ == '__main__':
    #print(university(dict(code=91224, city="Łódź", street="ALEKSANDROWSKA", buildingNumber=104)))
    print(criterions(code=91224, city="Łódź", street="ALEKSANDROWSKA", buildingNumber=104))
