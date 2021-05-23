# Adjust test task

_(c) feakuru, 2021_

This is a Flask application that was designed as a test task following [this specification](https://gist.github.com/kotik-adjust/4883e33c439db6de582fd0986939045c).

## Running the app

0. Install [pipenv](https://pipenv.pypa.io/en/latest/).
1. Run `pipenv install`
2. Run `FLASK_APP=server.py flask run`
3. The app will display how many entries are in the database and the default Flask log messages.
4. The app will be launched on port 5000 by default.

A few notes:
- the SQLite database file `adjust-task-db.db` will be created if it doesn't exist;
- the SQLite database will be dropped and recreated every time the server is launched - this was done for test purposes when implementing the server, but it has a nice side effect in that it provides the administrator with the ability to quickly upload new data using a CSV file;

## API

There is only one HTTP endpoint - the root endpoint. It accepts:
- The following field names to display for metric records (in the `fields` GET parameter, as a comma-separated list):
    - `date`
    - `channel`
    - `country`
    - `os`
    - `impressions`
    - `clicks`
    - `installs`
    - `spend`
    - `revenue`
    - `cpi`
- The following field names to group metric records by (in the `group_by` GET parameter, as a comma-separated list):
    - `date`
    - `channel`
    - `country`
    - `os`
- The following field names to order metric records by (in the `order_by` GET parameter, as a comma-separated list, preficed by `-` if the desired ordering is descending):
    - `date`
    - `channel`
    - `country`
    - `os`
    - `impressions`
    - `clicks`
    - `installs`
    - `spend`
    - `revenue`
    - `cpi`
- The following field names to filter metric records by:
    - `date_from` (`YYYY-MM-DD`, inclusive)
    - `date_to` (`YYYY-MM-DD`, inclusive)
    - `channel`
    - `country`
    - `os`

It then returns the resulting metric set as a JSON response in the following format:

```json
{
    "metrics": [
        {
            "date": "2017-05-01",
            "channel": "facebook",
            "country": "CA",
            "os": "ios",
            "clicks": 30255,
            "cpi": 58.74834351286322,
            "impressions": 996918,
            "installs": 5403,
            "revenue": 14553.660000000002,
            "spend": 317417.3
        },
        // ...
    ]
}
```

__NB__: fields `date`, `channel`, `country`, and `os` will appear in the results only if grouped by; the other fields will appear if specified in the `fields` parameter or if the `fields` parameter is not specified.

## URLs for common use cases

1. Show the number of impressions and clicks that occurred before the 1st of June 2017, broken down by channel and country, sorted by clicks in descending order:
```
    http://127.0.0.1:5000/?fields=impressions,clicks&date_to=2017-05-31&group_by=channel,country&order_by=-clicks
```


2. Show the number of installs that occurred in May of 2017 on iOS, broken down by date, sorted by date in ascending order:
```
    http://127.0.0.1:5000/?fields=installs&date_from=2017-05-01&date_to=2017-05-31&os=ios&group_by=date,os&order_by=date
```


3. Show revenue, earned on June 1, 2017 in US, broken down by operating system and sorted by revenue in descending order:
```
    http://127.0.0.1:5000/?fields=revenue&date_from=2017-06-01&date_to=2017-06-01&group_by=date,os&order_by=-revenue
```


4. Show CPI and spend for Canada (CA) broken down by channel ordered by CPI in descending order. Please think carefully which is an appropriate aggregate function for CPI:
```
    http://127.0.0.1:5000/?fields=cpi,spend&country=CA&group_by=channel&order_by=-cpi
```
