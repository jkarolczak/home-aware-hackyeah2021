import requests
import json

with open("connection.json", "r") as fp:
    config = json.loads(fp.read())
    


def __request(url: str, payload: dict) -> str:
    headers = {
        "BIK-OAPI-Key": config["BIK-OAPI-Key"],
        "Content-Type": "application/json"
    }
    response = requests.request(
        "POST", 
        url, 
        headers=headers, 
        data=payload,
        cert=(config["cert-crt"], config["cert-key"]),
        verify=False
    )
    try:
        assert response.status_code == 200
        return response.text
    except:
        raise Exception("¯\_(ツ)_/¯")
    

def __api4_nearest_poi(address: dict, poi_type: str) -> float:
    url = "https://gateway.oapi.bik.pl/bik-api-4/punkty-zainteresowania-adres"
    payload = json.dumps({
        "size": "100",
        "address": {
            "code": address["code"],
            "city": address["city"],
            "street": address["street"],
            "buildingNumber": address["buildingNumber"]
        },
        "nearestPOI": poi_type
    })
    return json.loads(__request(url, payload))["nearestPOI"]
    
def post_office(address: dict) -> float:
    return __api4_nearest_poi(address, "D_POCZTA")["D_POCZTA"]

address = {
    "code": 92221,
    "city": "Łódź",
    "street": "NOWOGRODZKA",
    "buildingNumber": 17
}
print(post_office(address))
