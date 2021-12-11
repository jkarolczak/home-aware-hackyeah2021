from io import SEEK_CUR
import requests
import json
import os

from urllib.parse import urljoin


with open("connection.json", "r") as fp:
    config = json.loads(fp.read())

cache_dir = config.get("cache_dir", ".cache")
if not os.path.exists(cache_dir):
    os.mkdir(cache_dir)


def _api(endpoint: str, payload: dict, base: str = "https://gateway.oapi.bik.pl/") -> str:
    # if endpoint + payload is cached in a file, read and return it
    headers = {
        "BIK-OAPI-Key": config["BIK-OAPI-Key"],
        "Content-Type": "application/json"
    }
    response = requests.request(
        "POST", 
        urljoin(base, endpoint), 
        headers=headers, 
        data=json.dumps(payload),
        cert=(config["cert-crt"], config["cert-key"]),
        verify=False
    )
    assert response.status_code == 200, f"API Error ({response.status_code}) ¯\_(ツ)_/¯"
    data = response.json()
    # TODO(max): cache `data` to some file
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

def post_office(address: dict) -> float:
    return _api4_nearest_poi(address, "D_POCZTA")["D_POCZTA"]

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

if __name__ == '__main__':
    address = {
        "code": 92221,
        "city": "Łódź",
        "street": "NOWOGRODZKA",
        "buildingNumber": 17
    }
    print(consumer_expenses(address))