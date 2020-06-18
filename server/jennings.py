import logging
import re
from datetime import timedelta

import requests
from bs4 import BeautifulSoup

import timeutils
from constants import JENNINGS_CODES, AOD_DIFFS


def fetch(startdate=0):
    output = {}
    get_time = timeutils.utc_now()

    for station in JENNINGS_CODES:
        request = BeautifulSoup(
            requests.get(
                f"https://thamestides.org.uk/dailytides2.php?statcode={JENNINGS_CODES[station]}"
                f"&startdate={get_time.date().strftime('%s') if startdate == 0 else startdate}"
            ).content,
            "html.parser",
        )
        output[station] = []
        table = request.find("table")
        if table is None:
            continue

        for row in table.find_all("tr"):
            # the PHP outputs <td> tags that are not closed, and this really messes with BeautifulSoup's parser...
            # so instead we make some assumptions and use RegEx. The RegEx removes all formatting tags, the <tr> tags
            # and the aod class styling, so only <td> tags are left, which we use to split the string into a list
            # The first element of the list will (hopefully) always be empty because <td> is the very first text on the
            # line, so we remove the first element (empty) from `children`
            children = re.sub(r"(</?(b|i|tr|br|/td)/?>| class=\"aod\")", '', str(row)).strip().split("<td>")[1:]

            # High tide values also contain a column for AOD heights. We don't need these, so we discard them.
            # children looks like this: ['Low',  '00:29', '0.8', '',    '01:00', '0.9', ''   ]
            #                           ['High', '06:27', '6.5', '3.3', '07:14', '6.2', '3.0']
            if "High" in children or "Low" in children:
                # sometimes (e.g. timestamp 1591192000) there will be a high tide one day and none the next, or
                # another odd combination. So first we must check that there are values for that low or high tide
                if children[1].strip() != '' and children[2].strip():
                    output[station].append([timeutils.time_to_unix_utc(get_time, children[1]),
                                            # Subtracting the height at Tower Pier / London Bridge gives us the AOD
                                            # height of the station. By adding the AOD delta for each station we get
                                            # the CD height for that location
                                            round(float(children[2]) - AOD_DIFFS["Tower"] + AOD_DIFFS[station], 2)])
                if children[4].strip() != '' and children[5].strip():
                    # we add another day because the second column is for tomorrow's high tides
                    output[station].append([timeutils.time_to_unix_utc(get_time + timedelta(days=1), children[4]),
                                            round(float(children[5]) - AOD_DIFFS["Tower"] + AOD_DIFFS[station], 2)])
        # sort by the timestamp of each turning point, for easy debugging and the prettiness factor
        output[station] = sorted(output[station], key=lambda x: x[0])

    logging.info("Fetched and processed tide time predictions from thamestides.org.uk")
    return output


if __name__ == "__main__":
    # some good start dates to try (because they have unusual order of tides)
    # 1591192000, 1592401600, 1593611200
    print(*fetch(startdate=0).values(), sep="\n")
