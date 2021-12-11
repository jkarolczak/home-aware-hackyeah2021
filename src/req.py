import requests
import json

from urllib.parse import urljoin

with open("connection.json", "r") as fp:
    config = json.loads(fp.read())


def __request(endpoint: str, payload: dict, base: str = "https://gateway.oapi.bik.pl") -> str:
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
    try:
        assert response.status_code == 200
        return response.json()
    except:
        raise Exception("¯\_(ツ)_/¯")
    

def __api4_nearest_poi(address: dict, poi_type: str) -> float:
    endpoint = "/bik-api-4/punkty-zainteresowania-adres"
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
    return __request(endpoint, payload)["nearestPOI"]
    
    
def post_office(address: dict) -> float:
    return __api4_nearest_poi(address, "D_POCZTA")["D_POCZTA"]


address = {
    "code": 92221,
    "city": "Łódź",
    "street": "NOWOGRODZKA",
    "buildingNumber": 17
}
print(post_office(address))
