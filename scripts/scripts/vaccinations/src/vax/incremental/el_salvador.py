from datetime import datetime
import locale
import json

import pandas as pd
import numpy as np
from bs4 import BeautifulSoup

from vax.utils.incremental import enrich_data, increment, clean_count
from vax.utils.utils import get_soup 


def read(source: str) -> pd.Series:
    soup = get_soup(source)
    link = parse_infogram_link(soup)
    soup = get_soup(link)
    infogram_data = parse_infogram_data(soup)
    return pd.Series({
        "people_vaccinated": parse_infogram_people_vaccinated(infogram_data),
        "date": parse_infogram_date(infogram_data),
        "source_url": source
    })
    
def parse_infogram_link(soup: BeautifulSoup) -> str:
    url_end = soup.find(class_="infogram-embed").get("data-id")
    return f"https://e.infogram.com/{url_end}"


def parse_infogram_data(soup: BeautifulSoup) -> dict:
    for script in soup.find_all("script"):
        if "infographicData" in str(script):
            json_data = (
                script.string[:-1]
                .replace("window.infographicData=", "")
            )
            json_data = json.loads(json_data)
            break
    return json_data


def parse_infogram_people_vaccinated(infogram_data: dict) -> int:
    ppl_vax = (
        infogram_data["elements"]["content"]["content"]["entities"]["c5ca046c-84e5-4ee1-a8b0-a408e1f5eb7f"]["props"]
        ["content"]["blocks"][0]["text"]
    )
    return clean_count(ppl_vax)


def parse_infogram_date(infogram_data: dict) -> str:
    x = (
        infogram_data["elements"]["content"]["content"]["entities"]["168106cd-505a-4f47-8618-21beb5a18499"]["props"]
        ["content"]["blocks"][0]["text"]
    )
    return datetime.strptime(x, "RESUMEN DE VACUNAS %d-%B-%y").strftime("%Y-%m-%d")


def enrich_location(ds: pd.Series) -> pd.Series:
    return enrich_data(ds, "location", "El Salvador")


def enrich_vaccine(ds: pd.Series) -> pd.Series:
    return enrich_data(ds, "vaccine", "Oxford/AstraZeneca")


def pipeline(ds: pd.Series) -> pd.Series:
    return (
        ds
        .pipe(enrich_location)
        .pipe(enrich_vaccine)
    )


def main():
    locale.setlocale(locale.LC_TIME, "es_ES")
    source = "https://covid19.gob.sv/"
    data = read(source).pipe(pipeline)
    increment(
        location=data["location"],
        total_vaccinations=np.nan,
        people_vaccinated=data["people_vaccinated"],
        date=data["date"],
        source_url=data["source_url"],
        vaccine=data["vaccine"]
    )


if __name__ == "__main__":
    main()