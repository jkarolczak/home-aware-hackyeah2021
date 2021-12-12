# hackyeah2021

## How to use

To use HomeAware, addresses of the houses interesting for the user should be loaded. To do that, enter addresses in the text fields accordingly and press “Add”. Here we’ve already added four locations, if you want to add your own just uncheck "Show demo locations" on the left panel.

![locations](static/locations.png)

The map shows where each address is located on the map of Łódź.

![map](static/map.png)

Then, User Profile should be set by choosing the user category and changing values of each criterion to match the user’s needs. 

![user-profile](static/user-profile.png)

If the user wants to use advanced options, they should press that option and  a list of other possibilities will unfold.

Users can choose for which category they can access its precise criterion, hidden by default. 

![advanced](static/advanced.png)

Finally, the app shows the final ranking of houses provided and shows the comparison of different criteria among them. The comparison is based on quartile values of each criterion - green dots mean that the location is better than the others, red dots mean that its worse than the others, and yellow dots signify indifference.

Additionally, an explanation for each address is provided, presenting the result on each category with a waterfall chart.

![analysis](static/analysis.png)

Additionally, an explanation for each address is provided, presenting the result on each category. After clicking "Show location details" on the left panel, the influence of all values (not summed into categories) can be shown.

![explanation](static/explanation.png)


## How to run

Install requirements.

```
pip install -r requirements.txt
```

Run app by executing the following command in the same directory as `README.md`.

```
streamlit run src/app.py
```

Run individual scripts as:

```
python -m src.res
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
