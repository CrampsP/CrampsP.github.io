import os
from city_coordinates import lat, long, names
from datetime import date, timedelta
import calendar
from openmeteopy import OpenMeteo
from openmeteopy.daily import DailyHistorical
from openmeteopy.options import HistoricalOptions
from openmeteopy.utils.constants import *


import glob

# Remove any previously generated per-city CSVs (pattern: daily_XX_name.csv, hourly_XX_name.csv)
patterns = ["daily_??_*.csv"]
found_any = False
for pattern in patterns:
    for path in glob.glob(pattern):
        found_any = True
        try:
            print(f"Found previous file '{path}'. Deleting...")
            os.remove(path)
            print(f"Deleted '{path}'")
        except Exception as e:
            print(f"Failed to delete '{path}': {e}")

if not found_any:
    print("No previous per-city daily/hourly CSV files found to delete.")


from typing import Iterable
import pandas as pd
import time
import re


# Helper to handle single value or list for lat/long
def as_iter(x) -> Iterable:
    if isinstance(x, (list, tuple)):
        return x
    return [x]


#yesterday = date.today() - timedelta(days=1)

# Initialize hourly or daily calls (templates)
daily = DailyHistorical()


lat_iter = as_iter(lat)
long_iter = as_iter(long)
# names may be a list of city names (matched to lat/long)
try:
    names_iter = as_iter(names)
except NameError:
    names_iter = [None] * len(lat_iter)

if len(lat_iter) != len(long_iter):
    raise ValueError("lat and long must have the same length")

# Ensure names_iter length matches lat/long by padding/truncating
if len(names_iter) != len(lat_iter):
    if len(names_iter) < len(lat_iter):
        names_iter = names_iter + [None] * (len(lat_iter) - len(names_iter))
    else:
        names_iter = names_iter[: len(lat_iter)]


def _sanitize_name(name: str, idx: int) -> str:
    """Return a filesystem-safe short name for the city.

    If name is falsy, returns city_{idx:02d}.
    Replaces non-alphanumeric characters with underscore.
    """
    if not name:
        return f"city_{idx:02d}"
    # keep letters, numbers, dot, dash, underscore
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(name))
    s = s.strip("_")
    if not s:
        return f"city_{idx:02d}"
    return s

saved_files = []

def fetch_all() -> str:
    """Fetch daily data for all configured lat/longs and concatenate into a single CSV.

    Returns the path to the combined CSV (daily_all_locations.csv) on success.
    """
    saved_files_local = []

    # Helper: attempt to fetch daily data with retries and exponential backoff
    def fetch_with_retries(opts, max_retries=3, backoff_base=1.5):
        attempt = 0
        while attempt < max_retries:
            attempt += 1
            try:
                meteod = OpenMeteo(opts, None, daily.all())
                dfd = meteod.get_pandas()
                return dfd, meteod
            except BaseException as e:
                # openmeteopy raises BaseException in some error paths; catch it
                wait = backoff_base * (2 ** (attempt - 1))
                print(f"Attempt {attempt} failed for ({opts.latitude},{opts.longitude}): {e}")
                if attempt < max_retries:
                    print(f"Retrying in {wait:.1f}s...")
                    time.sleep(wait)
                else:
                    print(f"Giving up after {max_retries} attempts for ({opts.latitude},{opts.longitude})")
                    return None, None

    for idx, (latitude, longitude) in enumerate(zip(lat_iter, long_iter), start=1):
        print(f"Processing #{idx}: lat={latitude}, long={longitude}")
        city_raw = names_iter[idx - 1] if idx - 1 < len(names_iter) else None
        city_safe = _sanitize_name(city_raw, idx)

        # Compute end_date as the most recent Saturday (last Saturday)
        # and start_date as the Sunday before that (6 days earlier), so the range is Sunday..Saturday (7 days)
        today = date.today()
        # weekday(): Monday=0 .. Sunday=6. Saturday is 5
        days_since_saturday = (today.weekday() - 5) % 7
        # If today is Saturday (days_since_saturday == 0), use previous Saturday (7 days ago)
        if days_since_saturday == 0:
            days_since_saturday = 7
        last_saturday = today - timedelta(days=days_since_saturday)
        start_sunday = last_saturday - timedelta(days=6)

        options = HistoricalOptions(
            latitude=latitude,
            longitude=longitude,
            start_date=start_sunday,
            end_date=last_saturday,
        )

        dfd, meteod = fetch_with_retries(options, max_retries=4, backoff_base=1.0)

        if dfd is None:
            # Skip saving for this city and continue with next
            print(f"Skipping city #{idx} due to repeated fetch errors: {latitude}, {longitude}")
        else:
            # Print small summary
            try:
                print(dfd.head())
            except Exception:
                pass

            # Save per-city CSV using sanitized city name
            try:
                daily_fname = f"daily_{idx:02d}_{city_safe}.csv"
                meteod.save_csv(daily_fname)
                print(f"Saved: {daily_fname}")
                # record saved file and metadata for later concatenation
                saved_files_local.append({
                    "path": daily_fname,
                    "city_idx": idx,
                    "city_name": city_raw,
                    "latitude": latitude,
                    "longitude": longitude,
                })
            except Exception as e:
                print(f"Failed saving CSVs for city #{idx} ({city_safe}): {e}")

        # Small delay between cities to reduce likelihood of hitting rate limits
        time.sleep(1.0)

    # After loop: concatenate all saved per-city CSVs into one DataFrame
    out_name = "daily_all_locations.csv"
    if saved_files_local:
        parts = []
        for info in saved_files_local:
            try:
                df = pd.read_csv(info["path"], index_col=0)
            except Exception as e:
                print(f"Failed reading {info['path']}: {e}")
                continue
            # Attach metadata columns
            df = df.copy()
            df["city_idx"] = info["city_idx"]
            df["city_name"] = info["city_name"]
            df["latitude"] = info["latitude"]
            df["longitude"] = info["longitude"]
            df["source_file"] = info["path"]
            parts.append(df)

        if parts:
            all_df = pd.concat(parts, axis=0, ignore_index=False)
            # Save combined CSV
            try:
                all_df.to_csv(out_name)
                print(f"Saved combined CSV: {out_name}")
            except Exception as e:
                print(f"Failed saving combined CSV {out_name}: {e}")
        else:
            print("No per-city CSVs could be read for concatenation.")
    else:
        print("No per-city CSVs were saved, skipping concatenation.")

    return out_name


if __name__ == "__main__":
    fetch_all()