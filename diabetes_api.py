# =============================================================================
# Problem Set 4: Using an API
# Diabetes in Jamaica vs. the rest of the Caribbean (and the US)
#
# Author: Tobianna Clarke
# Date:   November 14, 2026
#
# What this does:
#   1. asks the World Bank API for diabetes rates in a bunch of Caribbean
#      countries plus the US
#   2. cleans up what comes back (there are a LOT of empty years)
#   3. prints a ranked table for the newest year, compares Jamaica to the
#      Caribbean average and the US, and shows how Jamaica changed over time
#
# How to run:  python diabetes_api.py
# Needs:       pip install requests
# =============================================================================

import requests                    # for talking to the API over the internet

# the World Bank's code for "Diabetes prevalence (% of population ages 20 to 79)"
# (I found this by searching their indicator list for "diabetes")
INDICATOR = "SH.STA.DIAB.ZS"

# 3-letter country codes for the places I want to compare
# Jamaica first because that's home, then other Caribbean islands, then the US
COUNTRIES = ["JAM", "TTO", "BRB", "BHS", "HTI", "DOM", "CUB",
             "GUY", "BLZ", "PRI", "LCA", "GRD", "USA"]


def get_diabetes_data(country_codes):
    """
    Asks the World Bank API for the diabetes data for the countries I give it.

    Parameters
    ----------
    country_codes : list of str
        3-letter country codes, like ["JAM", "USA"].

    Returns
    -------
    list of dict
        One dictionary per country per year, straight from the API.
        Returns an empty list if something goes wrong.
    """
    # the API wants all the codes in one string separated by ; (like "JAM;USA")
    codes = ";".join(country_codes)
    url = "https://api.worldbank.org/v2/country/" + codes + "/indicator/" + INDICATOR

    # format=json so I get JSON back instead of XML
    # per_page=1000 so everything comes back in one page instead of 3 or 4
    settings = {"format": "json", "per_page": 1000}

    try:
        response = requests.get(url, params=settings, timeout=30)
    except requests.exceptions.RequestException:
        # this happens if there's no internet or the site is down
        print("Couldn't reach the World Bank API. Check your internet and try again.")
        return []

    # 200 means it worked, anything else means something went wrong
    if response.status_code != 200:
        print("The API sent back an error code:", response.status_code)
        return []

    data = response.json()

    # the World Bank sends back a list with 2 parts: [page info, the actual data]
    # if the second part is missing, there's nothing to use
    if len(data) < 2 or data[1] is None:
        print("The API didn't send back any data.")
        return []

    return data[1]


def clean_data(raw_records):
    """
    Throws out the empty years and organizes the data by country.

    Parameters
    ----------
    raw_records : list of dict
        The list that get_diabetes_data() returns.

    Returns
    -------
    dict
        Country name -> {year: diabetes %}, for example
        {"Jamaica": {2024: 12.5, 2011: 15.7}, ...}
    """
    cleaned = {}

    for record in raw_records:
        percent = record["value"]

        # most years are blank (None) because they only measure every few years,
        # so skip those
        if percent is None:
            continue

        # the name comes back as "Bahamas, The" so I take off the ", The" part
        country = record["country"]["value"].replace(", The", "")
        year = int(record["date"])   # the year comes back as text like "2024"

        # first time seeing this country, so give it an empty spot to fill in
        if country not in cleaned:
            cleaned[country] = {}

        cleaned[country][year] = percent

    return cleaned


def get_newest_values(cleaned):
    """
    Finds the most recent diabetes % for each country.

    Parameters
    ----------
    cleaned : dict
        The dictionary from clean_data().

    Returns
    -------
    list of tuple
        (percent, country, year) for each country, sorted highest to lowest.
    """
    newest = []

    for country in cleaned:
        years = cleaned[country]
        newest_year = max(years)          # biggest year = most recent
        percent = years[newest_year]
        newest.append((percent, country, newest_year))

    # putting the percent first in each tuple lets sort() order by percent
    # reverse=True so the highest is at the top
    newest.sort(reverse=True)
    return newest


def print_summary(newest, cleaned):
    """
    Prints a ranked table plus a few comparisons that focus on Jamaica.

    Parameters
    ----------
    newest : list of tuple
        The sorted list from get_newest_values().
    cleaned : dict
        The dictionary from clean_data() (used for Jamaica over time).
    """
    print("=" * 55)
    print("Diabetes prevalence (% of adults ages 20-79)")
    print("Most recent year with data, highest to lowest")
    print("=" * 55)

    caribbean_total = 0
    caribbean_count = 0
    jamaica_percent = None
    us_percent = None

    rank = 1
    for percent, country, year in newest:
        # put an arrow next to Jamaica so it's easy to spot
        if country == "Jamaica":
            arrow = "  <-- home"
        else:
            arrow = ""
        print(str(rank) + ". " + country + " (" + str(year) + "): " + str(percent) + "%" + arrow)
        rank = rank + 1

        # save Jamaica and the US for later, and add up everyone else
        # (the US doesn't count toward the Caribbean average)
        if country == "Jamaica":
            jamaica_percent = percent
        if country == "United States":
            us_percent = percent
        else:
            caribbean_total = caribbean_total + percent
            caribbean_count = caribbean_count + 1

    print()

    # only do the comparisons if Jamaica actually came back from the API
    if jamaica_percent is None:
        print("No data came back for Jamaica, so I can't compare.")
        return

    caribbean_average = caribbean_total / caribbean_count
    print("Caribbean average: " + str(round(caribbean_average, 1)) + "% (" + str(caribbean_count) + " countries)")
    print("Jamaica: " + str(jamaica_percent) + "%")

    # positive difference = Jamaica is higher, negative = Jamaica is lower
    difference = round(jamaica_percent - caribbean_average, 1)
    if difference > 0:
        print("Jamaica is " + str(difference) + " points ABOVE the Caribbean average")
    else:
        print("Jamaica is " + str(abs(difference)) + " points BELOW the Caribbean average")

    if us_percent is not None:
        print("United States: " + str(us_percent) + "%")

    # Jamaica over time (sorted() puts the years in order, oldest first)
    print()
    print("Jamaica over time:")
    jamaica_years = cleaned["Jamaica"]
    for year in sorted(jamaica_years):
        print("  " + str(year) + ": " + str(jamaica_years[year]) + "%")


# =============================================================================
# Main: run everything in order
# =============================================================================

if __name__ == "__main__":

    # step 1: get the data from the API
    raw_records = get_diabetes_data(COUNTRIES)

    # stop here if nothing came back, otherwise the rest would crash
    if len(raw_records) == 0:
        print("Nothing to show, stopping.")
    else:
        # step 2: clean it up
        cleaned = clean_data(raw_records)

        # step 3: find each country's newest value and print the summary
        newest = get_newest_values(cleaned)
        print_summary(newest, cleaned)
