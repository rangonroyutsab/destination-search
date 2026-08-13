import random

import pandas as pd

RANDOM_SEED = 42


def fill_missing_populations(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Ensure Population is numeric.
    df["Population"] = pd.to_numeric(
        df["Population"],
        errors="coerce",
    )

    # Normalize city names only for matching.
    df["_city_normalized"] = df["City"].astype("string").str.strip().str.lower()

    missing_before = df["Population"].isna().sum()

    print(f"Missing populations before: {missing_before:,}")

    # =========================================================
    # 1. LOCATION MATCH
    #    Country + Latitude + Longitude
    # =========================================================

    location_population = (
        df.dropna(subset=["Population"])
        .groupby(
            ["Country", "Latitude", "Longitude"],
            dropna=False,
        )["Population"]
        .median()
    )

    missing_mask = df["Population"].isna()

    location_keys = pd.MultiIndex.from_frame(
        df.loc[
            missing_mask,
            ["Country", "Latitude", "Longitude"],
        ]
    )

    location_values = location_population.reindex(location_keys).to_numpy()

    df.loc[missing_mask, "Population"] = location_values

    missing_after_location = df["Population"].isna().sum()

    print(f"Filled by location: {missing_before - missing_after_location:,}")

    # =========================================================
    # 2. CITY NAME MATCH
    #    Country + normalized City
    # =========================================================

    city_population = (
        df.dropna(subset=["Population"])
        .groupby(
            ["Country", "_city_normalized"],
            dropna=False,
        )["Population"]
        .median()
    )

    missing_mask = df["Population"].isna()

    city_keys = pd.MultiIndex.from_frame(
        df.loc[
            missing_mask,
            ["Country", "_city_normalized"],
        ]
    )

    city_values = city_population.reindex(city_keys).to_numpy()

    df.loc[missing_mask, "Population"] = city_values

    missing_after_city = df["Population"].isna().sum()

    print(f"Filled by city name: {missing_after_location - missing_after_city:,}")

    # =========================================================
    # 3. COUNTRY NAME MATCH
    #    Use median known city population within the country.
    # =========================================================

    country_population = (
        df.dropna(subset=["Population"]).groupby("Country")["Population"].median()
    )

    missing_mask = df["Population"].isna()

    df.loc[missing_mask, "Population"] = df.loc[missing_mask, "Country"].map(
        country_population
    )

    missing_after_country = df["Population"].isna().sum()

    print(f"Filled by country: {missing_after_city - missing_after_country:,}")

    # =========================================================
    # 4. RANDOM INTEGER
    #    Only rows for which absolutely nothing could be inferred.
    # =========================================================

    remaining_mask = df["Population"].isna()
    remaining_count = remaining_mask.sum()

    if remaining_count:
        known_populations = df["Population"].dropna()

        if known_populations.empty:
            random_min = 1
            random_max = 100_000
        else:
            random_min = max(1, int(known_populations.min()))
            random_max = int(known_populations.max())

        rng = random.Random(RANDOM_SEED)

        random_values = [
            rng.randint(random_min, random_max) for _ in range(remaining_count)
        ]

        df.loc[remaining_mask, "Population"] = random_values

    print(f"Filled randomly: {remaining_count:,}")

    # =========================================================
    # Final cleanup
    # =========================================================

    df["Population"] = df["Population"].round().astype("int64")

    df.drop(
        columns=["_city_normalized"],
        inplace=True,
    )

    missing_final = df["Population"].isna().sum()

    print(f"Missing populations after: {missing_final:,}")

    return df


df = pd.read_csv("data/country_name_filled/worldcitiespop.csv")

df = fill_missing_populations(df)

df.to_csv(
    "data/population_filled/worldcitiespop.csv",
    index=False,
)
