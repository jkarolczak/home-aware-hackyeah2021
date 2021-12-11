import requests
import json
import os
import warnings
import base64

from urllib.parse import urljoin
from time import time

warnings.filterwarnings("ignore", "1013: InsecureRequestWarning")

with open("connection.json", "r") as fp:
    _config = json.loads(fp.read())

_cache_dict = {}
_cache_dir = _config.get("cache_dir", ".cache")
if not os.path.exists(_cache_dir):
    os.mkdir(_cache_dir)


def _payload_hash(payload: str) -> str:
    return str(base64.b64encode(payload.encode("utf-8")), "utf-8")


def _api(endpoint: str, payload: dict, base: str = "https://gateway.oapi.bik.pl/") -> str:
    # if endpoint + payload is cached in a file, read and return it
    payload = json.dumps(payload)

    cache_file = os.path.join(_cache_dir, endpoint + '==' + _payload_hash(payload)) + '.json'
    if cache_file in _cache_dict:
        # level 1 cache
        # print('L1 CACHE', cache_file)
        return _cache_dict[cache_file]
    elif os.path.exists(cache_file):
        # level 2 cache
        # print('L2 CACHE', cache_file)
        with open(cache_file, "r") as f:
            data = json.load(f)
            _cache_dict[cache_file] = data
            return data

    response = requests.request("POST", urljoin(base, endpoint),
                                headers={
                                    "BIK-OAPI-Key": _config["BIK-OAPI-Key"],
                                    "Content-Type": "application/json"
                                },
                                data=payload,
                                cert=(_config["cert-crt"], _config["cert-key"]),
                                verify=False
                                )
    assert response.status_code == 200, f"API Error ({response.status_code}) ¯\_(ツ)_/¯"
    data = response.json()

    _cache_dict[cache_file] = data
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w") as f:
        f.write(json.dumps(data))

    return data


def _api4_nearest_poi(address: dict, poi_type: str) -> float:
    payload = {
        "size": "100",
        "address": {
            "code": address["code"],
            "city": address["city"],
            "street": address["street"],
            "buildingNumber": address["buildingNumber"]
        },
        "nearestPOI": poi_type
    }
    return _api("bik-api-4/punkty-zainteresowania-adres", payload)["nearestPOI"]


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
    print(time() - t, 'seconds')

    t = time()
    b = post_office(address)
    print(time() - t, 'seconds')

    t = time()
    c = post_office(address)
    print(time() - t, 'seconds')

    assert a == b == c
