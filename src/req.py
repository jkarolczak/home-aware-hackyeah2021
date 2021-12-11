from io import SEEK_CUR
import requests
import json
import os
import warnings
import base64

from collections import defaultdict
from frozendict import frozendict
from urllib.parse import urljoin
from time import time

warnings.filterwarnings("ignore", "1013: InsecureRequestWarning")

with open("connection.json", "r") as fp:
    _config = json.loads(fp.read())

_cache_dict = defaultdict(dict)
_cache_dir = _config.get("cache_dir", ".cache")
if not os.path.exists(_cache_dir):
    os.mkdir(_cache_dir)


def _payload_hash(payload: str) -> str:
    return str(hash(payload))
    


def _api(endpoint: str, payload: dict, base: str = "https://gateway.oapi.bik.pl/") -> str:
    # if endpoint + payload is cached in a file, read and return it

    payload_str = json.dumps(payload)
    cache_file = os.path.join(_cache_dir, f'{endpoint}=={_payload_hash(payload_str)}.json')
    if cache_file in _cache_dict:
        # level 1 cache
        # print('L1 CACHE', cache_file)
        return _cache_dict[endpoint][payload_str]
    elif os.path.exists(cache_file):
        # level 2 cache
        # print('L2 CACHE', cache_file)
        with open(cache_file, "r") as f:
            for line in f.readlines():
                data = json.loads(line)
                inp, out = data['input'], data['output']
                if payload == inp:
                    _cache_dict[endpoint][payload_str] = out
                    return data

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
    with open(cache_file, "a") as f:
        f.write(json.dumps(dict(input=payload, output=data), indent=0))
    return data


def _api4_nearest_poi(address: dict, poi_type: str) -> float:
    payload = {
        "size": "100",
        "address": address,
        "nearestPOI": poi_type
    }
    return _api("bik-api-4/punkty-zainteresowania-adres", payload)["nearestPOI"]


def _api4_number_poi(address: dict, poi_type: str) -> float:
    payload = {
        "size": "500",
        "address": address,
        "poinumber": poi_type
    }
    return _api("bik-api-4/liczba-poi-adres", payload)["poinumber"]
    
    
def _api4_demographic(address: dict, demographicData: str) -> float:
    payload = {
        "size": "100",
        "address": address,
        "demographicData": demographicData
    }
    return _api("/bik-api-4/dane-demograficzne-adres", payload)["demographicData"]
    
    
def _api6(address: dict, section: str) -> float:
    payload = {
        "size": "STAT_250M",
        "productCode": "ALL",
        "address": address,
        "section": section
    }
    return _api("bik-api-6/address", payload)["geostats"]    


def consumer_expenses(address: dict) -> float:
    payload = {
        "size": 100,
        "address": address,
        "wealth": "WK_RAZEM"
    }
    return _api("/bik-api-4/zamoznosc-adres", payload)["wealth"]["WK_RAZEM"]


def _api10_address_point(address: dict, address_point: str) -> float:
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


def _api10_area_statistic(address: dict, area_statistic: str) -> float:
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


def post_office(address: dict) -> float:
    return _api4_nearest_poi(address, "D_POCZTA")["D_POCZTA"]


def _api3_safety(address: dict) -> dict:
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


def crimes(data: dict) -> float:
    return sum(data["details"].values())


def price(data: dict) -> float:
    return data["details"]["offer_price"]


def car_collisions(data: dict) -> float:
    return data["details"]["hitting_a_pedestrian"]


def price_and_safety(address: dict) -> (float, float, float):
    data = _api3_safety(address)
    return price(data[0]), crimes(data[1]), car_collisions(data[2])


def culture_entertainment(address: dict) -> float:
    pois = [
        "D_ROZRYWKA_I_KULTURA_KINO",
        "D_ROZRYWKA_I_KULTURA_KREGIELNIE",
        "D_ROZRYWKA_I_KULTURA_MUZEUM",
        "D_ROZRYWKA_I_KULTURA_TEATR"
    ]
    distances = [_api4_nearest_poi(address, poi)[poi] for poi in pois]
    return sum(distances) / len(distances)


def mall(address: dict) -> float:
    return _api4_nearest_poi(address, "D_CENTRUM_HANDLOWE")["D_CENTRUM_HANDLOWE"]


def health(address: dict) -> float:
    return _api4_nearest_poi(address, "D_ZDROWIE")["D_ZDROWIE"]


def railway_station(address: dict) -> float:
    return _api4_nearest_poi(address, "D_TRANSPORT_PKP_PRZYSTANEK_LUB_STACJA_DWORZEC")["D_TRANSPORT_PKP_PRZYSTANEK_LUB_STACJA_DWORZEC"]


def bus_stop(address: dict) -> float:
    return _api4_nearest_poi(address, "D_TRANSPORT_PRZYSTANEK_AUTOBUSOWY")["D_TRANSPORT_PRZYSTANEK_AUTOBUSOWY"]


def tram_stop(address: dict) -> float:
    return _api4_nearest_poi(address, "D_TRANSPORT_PRZYSTANEK_TRAMWAJOWY")["D_TRANSPORT_PRZYSTANEK_TRAMWAJOWY"]


def civil_services(address: dict) -> float:
    fire_stations = [
        "D_URZAD_I_SLUZBA_PUBLICZNA_SLUZBY_PUBLICZNE_OCHOTNICZA_STRAZ_POZARNA",
        "D_URZAD_I_SLUZBA_PUBLICZNA_SLUZBY_PUBLICZNE_STRAZ_POZARNA"
    ]
    fire_stations = [_api4_nearest_poi(address, poi)[poi] for poi in fire_stations]
    police = _api4_nearest_poi(address, "D_URZAD_I_SLUZBA_PUBLICZNA_SLUZBY_PUBLICZNE_KOMENDA_POLICJI")["D_URZAD_I_SLUZBA_PUBLICZNA_SLUZBY_PUBLICZNE_KOMENDA_POLICJI"]
    return (min(fire_stations) + police) / 2


def airports(address: dict) -> float:
    return _api4_nearest_poi(address, "D_TRANSPORT_LOTNISKO_MIEDZYNARODOWE")["D_TRANSPORT_LOTNISKO_MIEDZYNARODOWE"]


def worship(address: dict) -> float:
    return _api4_nearest_poi(address, "D_MIEJSCE_KULTU_KOSCIOL")["D_MIEJSCE_KULTU_KOSCIOL"]


def university(address: dict) -> float:
    return _api4_nearest_poi(address, "D_EDUKACJA_WYZSZE_SZKOLY_PUBLICZNE")["D_EDUKACJA_WYZSZE_SZKOLY_PUBLICZNE"]


def parcel_lockers(address: dict) -> float:
    return _api4_nearest_poi(address, "D_PRZESYLKI_PACZKOMAT")["D_PRZESYLKI_PACZKOMAT"]


def education(address: dict) -> float:
    pois = [
        "EDUKACJA_PRZEDSZKOLA_I_PUNKTY_PRZEDSZKOLNE",
        "EDUKACJA_SZKOLY_PODSTAWOWE",
        "EDUKACJA_LICEA_OGOLNOKSZTALCACE_I_PROFILOWANE",
        "EDUKACJA_ZESPOL_SZKOL",
        "EDUKACJA_TECHNIKA",
        "EDUKACJA_SZKOLY_BRANZOWE",
    ]
    return sum([_api4_number_poi(address, poi)[poi] for poi in pois])


def between_20_30(address: dict) -> float:
    groups = [
        "POPT2024",
        "POPT2529"
    ]
    return sum([_api4_demographic(address, group)[group] for group in groups])


def over_60(address: dict) -> float:
    groups = [
        "POPT6064",
        "POPT6569",
        "POPT7074",
        "POPT7599"
    ]
    return sum([_api4_demographic(address, group)[group] for group in groups])


def geoscore(address: dict) -> float:
    return _api("bik-api-5/geoscore-adres", address)["score"]


def cr3(address: dict) -> tuple:
    return _api6(address, "SR_CR3_KREDYTOBIORCY")[0]["result"]
    
    
def coordinates(address: dict) -> tuple:
    result = _api6(address, "SR_CR3_KREDYTOBIORCY")[0]["inputDataCoordinates"]
    return result["utm_x"], result["utm_y"]


def railway_tracks(address: dict) -> float:
    return _api10_address_point(address, "odl_tory")["odl_tory"]


def freeways(address: dict) -> float:
    return min(_api10_address_point(address, "odl_autost")["odl_autost"],
               _api10_address_point(address, "odl_drEksp")["odl_drEksp"])


def garages(address: dict) -> float:
    return _api10_area_statistic(address, "garaze")["garaze"]


def nature(address: dict) -> float:
    return min(_api10_area_statistic(address, "lasy")["lasy"], _api10_area_statistic(address, "zielen_mi")["zielen_mi"])


if __name__ == '__main__':
    address = {
        "code": 92221,
        "city": "Łódź",
        "street": "NOWOGRODZKA",
        "buildingNumber": 17
    }
    t = time()
    a = post_office(address)
    #a = price_and_safety(address)
    print(time() - t, 'seconds')
    b = post_office(address)
    #b = price_and_safety(address)
    print(time() - t, 'seconds')

    t = time()
    c = post_office(address)
    #c = price_and_safety(address)
    print(time() - t, 'secons')
    print(c)
    assert a == b == c
