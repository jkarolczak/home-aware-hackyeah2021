# hackyeah2021

## How to run

Install requirements.

```
pip install -r requirements.txt
```

Run app by executing the following command in the same directory as `README.md`.

```
streamlit run src/app.py
```

## Certificates
Certificate:
```
openssl pkcs12 -in srodmiescie4.pfx -clcerts -nokeys -out src/srodmiescie4.crt
```

Key:
```
openssl pkcs12 -in srodmiescie4.pfx -nocerts -nodes -out srodmiescie4.key
```
