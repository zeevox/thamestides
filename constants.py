# update .gitignore appropriately if making changes to these
DB_NAME = "thamestides.db"

# to calculate the Ordnance Datum values we use these, they are hardcoded and constant
# from the PLA Annual Tide Tables, p33: https://www.pla.co.uk/assets/PLA-Tide-Tables-2020.pdf
# these values represent how much lower Chart Datum is than Ordnance Datum at each location
AOD_DIFFS = {
    "Walton": 2.16,
    "Margate": 2.50,
    "Southend": 2.90,
    "Thameshaven": 3.05,
    "Tilbury": 3.12,
    "Silvertown": 3.35,
    "Charlton": 3.35,
    "Tower": 3.20,
    "Blackfriars": 3.05,
    "Westminster": 2.90,
    "Vauxhall": 2.59,
    "Chelsea": 2.44,
    "Albert": 2.29,
    "Wandsworth": 2.13,
    "Putney": 1.98,
    "Hammersmith": 1.68,
    "Barnes": 1.37,
    "Chiswick": 1.22,
    "Kew": 1.07,
    "Brentford": 0.91,
    "Richmond": 0.61,
}

# The codes used to access tide times predictions on ThamesTides.org.uk
# format https://thamestides.org.uk/dailytides2.php?statcode=<code>&startdate=0
# the startdate parameter allows getting historical values from 1 Jan 2014 (1388600000)
JENNINGS_CODES = {
    # "Tower": "LON",  # Provided by PLA to greater degree of accuracy
    "Putney": "PUT",
    "Chiswick": "CHI",
    "Kew": "STR",
    "Brentford": "BRE",
    # "Richmond": "RIC",  # Provided by PLA to greater degree of accuracy
}

UKHO_CODES = {
    "Southend": "0110",
    "Thameshaven": "0110A",
    "Tilbury": "0111",
    "Gravesend": "0111A",
    "Erith": "0111B",
    "Charlton": "0112",
    "Tower": "0113",
    "Chelsea": "0113A",
    "Albert": "0114",
    "Hammersmith": "0115",
    "Kew": "0115A",
    "Richmond": "0116",
}
