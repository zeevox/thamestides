# Thames Tides

![GitHub last commit](https://img.shields.io/github/last-commit/ZeevoX/thamestides)
[![Maintainability](https://api.codeclimate.com/v1/badges/7a39a65b4802fceb8d7a/maintainability)](https://codeclimate.com/github/ZeevoX/thamestides/maintainability)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/3c22a7aad7564dc083adfe673eb5e2d0)](https://www.codacy.com/manual/ZeevoX/thamestides?utm_source=github.com&utm_medium=referral&utm_content=ZeevoX/thamestides&utm_campaign=Badge_Grade)

## Introduction

-   The [Port of London Authority](http://www.pla.co.uk/hydrographics/ltoverview.cfm) maintains 12 tide gauges along the tidal stretch of the Thames and provides live readings, updated every minute and predicted tidal information.
-   [ThamesTides.org.uk](http://thamestides.org.uk/today) provides tide times and height predictions for locations between Chiswick and Richmond Lock, namely Putney, Chiswick, Strand-on-the-Green, Brentford.
-   The UK Hydrographic Office provides tide times and height predictions for locations along the Thames, namely [Albert Bridge](http://www.ukho.gov.uk/easytide/EasyTide/ShowPrediction.aspx?PortID=0114&PredictionLength=7), [Chelsea Bridge](http://www.ukho.gov.uk/easytide/EasyTide/ShowPrediction.aspx?PortID=0113A&PredictionLength=7), [Hammersmith Bridge](http://www.ukho.gov.uk/easytide/EasyTide/SelectPrediction.aspx?PortID=0115) and [Kew Bridge](http://www.ukho.gov.uk/easytide/EasyTide/ShowPrediction.aspx?PortID=0115A&PredictionLength=7) (among others).
-   The [Environment Agency](https://environment.data.gov.uk/flood-monitoring/id/measures/3400TH-flow--i-15_min-m3_s) provides Kingston flow gauge data, updated every 15 minutes.

## Coding project outline

-   Scrape data and aggregate it using Python:
    -   Fetch tidal gauge data every minute and save it into a SQL database
    -   Fetch tide times and height predictions and save it into a SQL database
-   Serve the collected data through PHP on my web server:
    -   Calculate [*Above Ordnance Datum*](http://thamestides.org.uk/AOD) land heights where necessary
    -   Calculate current tide rise speed
    -   Calculate whether the Thames Barrier is closed based on the difference between the readings on the Silvertown and Charlton PLA tide gauges
    -   Output this information in JSON format
-   Add tidal information to my [Home Assistant](https://www.home-assistant.io/) dashboard (it parses JSON)
-   [TBC] create a pretty HTML page that fetches the JSON from my PHP script using Javascript and neatly presents the information

## Installation and usage

```shell script
git clone https://github.com/ZeevoX/thamestides.git && cd thamestides
```

### Python data collection server

#### Dependencies

-   [pytz](https://pypi.org/project/pytz/)
-   [requests](https://pypi.org/project/requests/)
-   [apscheduler](https://pypi.org/project/APScheduler/)
-   [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)

```shell script
python3 -m pip install pytz requests apscheduler beautifulsoup4
```

#### Usage

Quick start (Linux):

```shell script
./thamestides
```

Command line options:

```shell script
~/thamestides$ python3 server/main.py -h
usage: main.py [-h] [-l LOGLEVEL] [-o LOGFILE]

Monitor the tidal stretch of the River Thames

optional arguments:
  -h, --help            show this help message and exit
  -l LOGLEVEL, --log LOGLEVEL
                        Set the logging level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
  -o LOGFILE, --output LOGFILE
                        Output to a log file
```

#### Starting the data collector as a daemon (Linux)

NB: [supervisord](http://supervisord.org/) required

```shell script
# create a process configuration file, enable the daemon and start it
./daemon enable

# check whether the daemon is currently running
./daemon status

# open the daemon's log file (scrollable; uses `less`)
./daemon log

# self-explanatory
./daemon start
./daemon stop
./daemon restart

# stop the daemon and remove its configuration files
./daemon disable
```

### PHP JSON API

This repository does not document how to set up a PHP web server.
Make sure the `thamestides` directory is accessible through your web server of choice for this to work. 
I test this project on `Apache/2.4.41` with `PHP 7.4.3`.

NB: Requires PHP >= 7.0

#### API reference

If you send bad JSON or request invalid data the server will attempt to respond with an appropriate response code and error message, but this is not guaranteed.

| URL parameter   |  Since  |   Type   | Description                                                                                                                                                         |
| --------------- | :-----: | :------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| predictions     | `0.0.1` |    any   | if set, fetch predicted data for the requested stations                                                                                                             |
| readings        | `0.0.1` |    any   | if set, fetch historical measurements for the requested stations                                                                                                    |
| station         | `0.0.1` |  string  | name of tidal station for which to fetch data; equivalent to `stations` with one item; this parameter overrides `stations` if both `station` and `stations` are set |
| stations        | `0.0.1` |  string  | comma-delimited, spaceless string list of tidal stations for which to fetch data or `all` to get all available stations                                             |
| last_n          | `0.0.1` |    int   | positive integer representing the maximum number of rows of data to output from the database                                                                        |
| start           | `0.0.1` | datetime | optional parsable datetime string representing the start time of the period of data to fetch; to be used in conjunction with `end`; default = 24 hours ago          |
| end             | `0.0.1` | datetime | optional parsable datetime string representing the end time of the period of data to fetch; to be used in conjunction with `start`; default = now                   |
| filter_non_null | `0.0.1` |    any   | if set, remove NULL values from measurements (e.g. when data unavailable for that time period or gauge was offline)                                                 |