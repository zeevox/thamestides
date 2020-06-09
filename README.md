# Thames Tides
## Introduction
* The [Port of London Authority](http://www.pla.co.uk/hydrographics/ltoverview.cfm) maintains 12 tide gauges along the tidal stretch of the Thames and provides live readings, updated every minute and predicted tidal information.
* [ThamesTides.org.uk](http://thamestides.org.uk/today) provides tide times and height predictions for locations between Chiswick and Richmond Lock, namely Putney, Chiswick, Strand-on-the-Green, Brentford.
* The UK Hydrographic Office provides tide times and height predictions for locations along the Thames, namely [Albert Bridge](http://www.ukho.gov.uk/easytide/EasyTide/ShowPrediction.aspx?PortID=0114&PredictionLength=7), [Chelsea Bridge](http://www.ukho.gov.uk/easytide/EasyTide/ShowPrediction.aspx?PortID=0113A&PredictionLength=7), [Hammersmith Bridge](http://www.ukho.gov.uk/easytide/EasyTide/SelectPrediction.aspx?PortID=0115) and [Kew Bridge](http://www.ukho.gov.uk/easytide/EasyTide/ShowPrediction.aspx?PortID=0115A&PredictionLength=7) (among others).
* The [Environment Agency](https://environment.data.gov.uk/flood-monitoring/id/measures/3400TH-flow--i-15_min-m3_s) provides Kingston flow gauge data, updated every 15 minutes.
## Coding project outline
* Scrape data and aggregate it using Python:
   * Fetch tidal gauge data every minute and save it into a SQL database
   * Fetch tide times and height predictions and save it into a SQL database
* Serve the collected data through PHP on my web server:
   * Calculate [_Above Ordnance Datum_](http://thamestides.org.uk/AOD) land heights where necessary
   * Calculate current tide rise speed
   * Calculate whether the Thames Barrier is closed based on the difference between the readings on the Silvertown and Charlton PLA tide gauges
   * Output this information in JSON format
* Add tidal information to my [Home Assistant](https://www.home-assistant.io/) dashboard (it parses JSON)
* [TBC] create a pretty HTML page that fetches the JSON from my PHP script using Javascript and neatly presents the information