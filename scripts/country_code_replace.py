from pathlib import Path

import pandas as pd
import pycountry

INPUT_FILE = Path("data/worldcitiespop.csv")
OUTPUT_FILE = Path("data/test.csv")

# Use this only for non-standard codes or when you want
# a different display name than pycountry provides.
COUNTRY_OVERRIDES = {
    "ad": "Andorra",
    "ae": "United Arab Emirates",
    "af": "Afghanistan",
    "ag": "Antigua and Barbuda",
    "ai": "Anguilla",
    "al": "Albania",
    "am": "Armenia",
    "an": "Netherlands Antilles",
    "ao": "Angola",
    "ar": "Argentina",
    "at": "Austria",
    "au": "Australia",
    "aw": "Aruba",
    "az": "Azerbaijan",
    "ba": "Bosnia and Herzegovina",
    "bb": "Barbados",
    "bd": "Bangladesh",
    "be": "Belgium",
    "bf": "Burkina Faso",
    "bg": "Bulgaria",
    "bh": "Bahrain",
    "bi": "Burundi",
    "bj": "Benin",
    "bm": "Bermuda",
    "bn": "Brunei Darussalam",
    "bo": "Bolivia",
    "br": "Brazil",
    "bs": "Bahamas",
    "bt": "Bhutan",
    "bw": "Botswana",
    "by": "Belarus",
    "bz": "Belize",
    "ca": "Canada",
    "cc": "Cocos Islands",
    "cd": "Congo DR",
    "cf": "Central African Republic",
    "cg": "Congo",
    "ch": "Switzerland",
    "ci": "Ivory Coast",
    "ck": "Cook Islands",
    "cl": "Chile",
    "cm": "Cameroon",
    "cn": "China",
    "co": "Colombia",
    "cr": "Costa Rica",
    "cu": "Cuba",
    "cv": "Cabo Verde",
    "cx": "Christmas Island",
    "cy": "Cyprus",
    "cz": "Czechia",
    "de": "Germany",
    "dj": "Djibouti",
    "dk": "Denmark",
    "dm": "Dominica",
    "do": "Dominican Republic",
    "dz": "Algeria",
    "ec": "Ecuador",
    "ee": "Estonia",
    "eg": "Egypt",
    "eh": "Western Sahara",
    "er": "Eritrea",
    "es": "Spain",
    "et": "Ethiopia",
    "fi": "Finland",
    "fj": "Fiji",
    "fk": "Falkland Islands",
    "fm": "Micronesia",
    "fo": "Faroe Islands",
    "fr": "France",
    "ga": "Gabon",
    "gb": "United Kingdom",
    "gd": "Grenada",
    "ge": "Georgia",
    "gf": "French Guiana",
    "gg": "Guernsey",
    "gh": "Ghana",
    "gi": "Gibraltar",
    "gl": "Greenland",
    "gm": "Gambia",
    "gn": "Guinea",
    "gp": "Guadeloupe",
    "gq": "Equatorial Guinea",
    "gr": "Greece",
}


def get_country_name(code: str) -> str | None:
    """
    Convert an ISO 3166-1 alpha-2 country code to its country name.

    Returns None when the code cannot be resolved.
    """

    normalized_code = code.strip().lower()

    # Check our custom mappings first.
    if normalized_code in COUNTRY_OVERRIDES:
        return COUNTRY_OVERRIDES[normalized_code]

    country = pycountry.countries.get(alpha_2=normalized_code.upper())

    if country is None:
        return None

    return country.name


def main() -> None:
    # ---------------------------------------------------------
    # 1. Read dataset
    # ---------------------------------------------------------
    df = pd.read_csv(INPUT_FILE)

    if "Country" not in df.columns:
        raise ValueError("CSV does not contain a 'Country' column.")

    # ---------------------------------------------------------
    # 2. Get unique country codes
    # ---------------------------------------------------------
    unique_codes = sorted(
        df["Country"].dropna().astype(str).str.strip().str.lower().unique()
    )

    print(f"Rows: {len(df):,}")
    print(f"Unique country codes: {len(unique_codes)}")
    print()

    # ---------------------------------------------------------
    # 3. Build the mapping only once
    # ---------------------------------------------------------
    country_mapping = {code: get_country_name(code) for code in unique_codes}

    print("\nResolved country codes:")
    for code in unique_codes:
        country = pycountry.countries.get(alpha_2=code.upper())

        if country:
            print(f'    "{code}": "{country.name}",')
        else:
            print(f'    "{code}": "UNKNOWN",')

    # ---------------------------------------------------------
    # 4. Find unrecognized country codes
    # ---------------------------------------------------------
    unknown_codes = [
        code for code, country_name in country_mapping.items() if country_name is None
    ]

    if unknown_codes:
        print("Unknown country codes found:")
        for code in unknown_codes:
            print(f"  - {code}")

        print()
        print("Add these codes to COUNTRY_OVERRIDES before running the conversion.")

        return

    # ---------------------------------------------------------
    # 5. Show the mapping
    # ---------------------------------------------------------
    print("Country mapping:")
    for code, country_name in country_mapping.items():
        print(f"  {code} -> {country_name}")

    print()

    # ---------------------------------------------------------
    # 6. Normalize the Country column
    # ---------------------------------------------------------
    normalized_country_codes = df["Country"].astype("string").str.strip().str.lower()

    # ---------------------------------------------------------
    # 7. Replace codes with country names
    # ---------------------------------------------------------
    df["Country"] = normalized_country_codes.map(country_mapping)

    # ---------------------------------------------------------
    # 8. Write the cleaned dataset
    # ---------------------------------------------------------
    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(f"Converted {len(df):,} rows.")
    print(f"Output written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
