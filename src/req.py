import requests
import json

url = "https://gateway.oapi.bik.pl/bik-api-4/punkty-zainteresowania-adres"

with open('connection.json', 'r') as fp:
    config = json.loads(fp.read())
    
payload = json.dumps({
  "size": "100",
  "address": {
    "code": 92221,
    "city": "Łódź",
    "street": "NOWOGRODZKA",
    "buildingNumber": 17
  },
  "nearestPOI": "D_ZDROWIE"
})
headers = {
  'BIK-OAPI-Key': config['BIK-OAPI-Key'],
  'Content-Type': 'application/json'
}

response = requests.request(
    "POST", 
    url, 
    headers=headers, 
    data=payload,
    cert=(config['cert-crt'], config['cert-key']),
    verify=False
)

print(response.text)
