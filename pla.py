import requests
import pytz
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from constants import aod_diffs


def fetch():
    get_time = pytz.utc.localize(datetime.utcnow())
    request = BeautifulSoup(
        requests.get(
            "https://www.pla.co.uk/hydrographics/ltoverview_table.cfm"
        ).content,
        "html.parser",
    )

    output_pla = {}

    for row in request.find("tbody").find_all("tr"):
        children = row.find_all("td")
        tide_gauge_name = children[0].get_text().strip()

        hw, lw = (
            children[4].get_text().strip().split(" "),
            children[5].get_text().strip().split(" "),
        )

        tomorrow = get_time + timedelta(days=1)
        hw_time = datetime.strptime(f"{hw[0]} GMT", "%H:%M %Z").time()
        lw_time = datetime.strptime(f"{lw[0]} GMT", "%H:%M %Z").time()
        hw[0] = pytz.utc.localize(
            datetime.combine(
                tomorrow.date() if hw_time < get_time.time() else get_time.date(),
                hw_time,
            )
        )
        lw[0] = pytz.utc.localize(
            datetime.combine(
                tomorrow.date() if lw_time < get_time.time() else get_time.date(),
                lw_time,
            )
        )

        output = {
            "time": int(get_time.strftime("%s")),
            "gauge_name": tide_gauge_name,
            "next_hw_time": int(hw[0].strftime("%s")),
            "next_hw_cd": float(hw[1][1:-2]),
            "next_lw_time": int(lw[0].strftime("%s")),
            "next_lw_cd": float(lw[1][1:-2]),
        }

        try:
            readings = {
                "observed_cd": float(children[1].get_text().strip()),
                "predicted_cd": float(children[2].get_text().strip()),
                "surge": float(children[3].get_text().strip()),
            }
            output = {**output, **readings}  # merge the two dictionaries
        except ValueError:
            print(
                f"ERR: Could not parse gauge data, {tide_gauge_name} gauge is probably offline."
            )
            output["status"] = 0
        else:
            output["status"] = 1

        if tide_gauge_name in aod_diffs:
            aod_readings = {
                "observed_aod": round(
                    output["observed_cd"] - aod_diffs[tide_gauge_name], 2
                ),
                "predicted_aod": round(
                    output["predicted_cd"] - aod_diffs[tide_gauge_name], 2
                ),
                "next_hw_aod": round(
                    output["next_hw_cd"] - aod_diffs[tide_gauge_name], 2
                ),
                "next_lw_aod": round(
                    output["next_lw_cd"] - aod_diffs[tide_gauge_name], 2
                ),
            }
            output = {**output, **aod_readings}

        output_pla[tide_gauge_name] = output
    return output_pla


if __name__ == "__main__":
    print(*fetch().values(), sep="\n")
