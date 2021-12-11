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
        "address": {
            "code": address["code"],
            "city": address["city"],
            "street": address["street"],
            "buildingNumber": address["buildingNumber"]
        },
        "nearestPOI": poi_type
    }
    return _api("bik-api-4/punkty-zainteresowania-adres", payload)["nearestPOI"]
    
    
def post_office(address: dict) -> float:
    return _api4_nearest_poi(address, "D_POCZTA")["D_POCZTA"]


if __name__ == '__main__':
    address = {
        "code": 92221,
        "city": "Łódź",
        "street": "NOWOGRODZKA",
        "buildingNumber": 17
    }
    print(post_office(address))

