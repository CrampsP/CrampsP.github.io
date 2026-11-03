import math
import pandas as pd

df = pd.read_csv("data.txt")
print(df)

pi = math.pi



def main():
        name = df.iloc[:, 0]
        rad = df.iloc[:, 1]
        hgt = df.iloc[:, 2]

        results = []

        for i in range(len(rad)):
            eff = storage_efficiency(rad[i], hgt[i])
            results.append((name[i], eff))

        sorted_results = sorted(results, key=lambda x : x[1], reverse = True)

        for n, eff in sorted_results:
            print(f"{n}: {eff}")
        


def storage_efficiency(hgt, rad):
    vol = compute_volume(hgt, rad)
    sa = compute_surface_area(hgt, rad)
    se = vol/sa
    return se


def compute_volume(hgt, rad):
    vol = pi*(rad ** 2)*hgt
    return vol

def compute_surface_area(hgt, rad):
    sa = 2*pi*rad*(rad+hgt)
    return sa

main()
