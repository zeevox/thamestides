import logging
from datetime import timedelta

import requests
from bs4 import BeautifulSoup

import timeutils
from constants import UKHO_CODES


def fetch():
    output = {}
    get_time = timeutils.utc_now()

    for station_name in UKHO_CODES:
        url = f"http://www.ukho.gov.uk/easytide/EasyTide/ShowPrediction.aspx?PortID={UKHO_CODES[station_name]}" \
              f"&PredictionLength=2&DaylightSavingOffset=0&PrinterFriendly=True&HeightUnits=0&GraphSize=7"

        request = BeautifulSoup(
            requests.get(url).content,
            "html.parser",
        )

        output[station_name] = []

        table_today, table_tomorrow = request.find(id="_ctl1_HWLWTable1_pnlHWLW").find_all("table")
        if table_today is None or table_tomorrow is None:
            continue

        today, tomorrow = table_today.find_all("tr"), table_tomorrow.find_all("tr")
        times = [
            *[timeutils.time_to_unix_utc(get_time, child.get_text().strip(), ts_tz="UTC")
              for child in today[2].find_all("td")],
            *[timeutils.time_to_unix_utc(get_time + timedelta(days=1), child.get_text().strip(), ts_tz="UTC")
              for child in tomorrow[2].find_all("td")],
        ]
        heights = [round(float(child.get_text().strip().replace(u'\xa0m', '')), 2)
                   for child in [*today[3].find_all("td"), *tomorrow[3].find_all("td")]]

        if len(times) != len(heights):
            logging.error("Unequal number of tide heights and times from the UKHO")
        for i in range(len(times)):
            output[station_name].append([times[i], heights[i]])

        output[station_name].sort()

    logging.info("Fetched and processed tide time predictions from the UKHO")
    return output


if __name__ == "__main__":
    for key, value in fetch().items():
        print(f"\"{key}\" => {value},", sep="\n")
