# lat_long_pairs.py - outline

names = [
    "New York-NY",
    "Los Angeles-CA",
    "Chicago-IL",
    "Houston-TX",
    "Phoenix-AZ",
    "Philadelphia-PA",
    "San Antonio-TX",
    "San Diego-CA",
    "Dallas-TX",
    "San Jose-CA"
]



# 1) Data: 10 latitudes and 10 longitudes (index-matched)
lat = [
    40.712776, 34.052235, 41.878113, 29.760427, 33.448376, 39.952583,
    29.424122, 32.715736, 32.776665, 37.338207
]

long = [
   -74.005974, -118.243683, -87.629799, -95.369804, -112.074036, -75.165222,
    -98.493629, -117.161087, -96.796988, -121.886330
]

# 2) Validation
assert len(lat) == 10, "lat must contain 10 values"
assert len(long) == 10, "long must contain 10 values"

# 3) Pair generator
def pairs():
    for la, lo in zip(lat, long):
        yield la, lo

# 4) Example usage
if __name__ == "__main__":
    for i, (la, lo) in enumerate(pairs(), start=1):
        print(f"{i:02d}: lat={la}, long={lo}")
