import pandas as pd
import numpy as np

# Participants
participants = ["Alice", "Ben", "Carlos", "Diana"]

# Factors
caffeine_levels = ["0", "50", "100"]  # mg
distractions = ["None", "Audio", "Visual", "Audio+Visual"]

# Baseline distribution (from graph)
baseline_mean = 200
baseline_sd = 15

# Adjustments
caffeine_effect = {"0": 0, "50": -10, "100": -20}  # lower reaction time = faster
distraction_effect = {"None": 0, "Audio": 15, "Visual": 20, "Audio+Visual": 35}

# Create dataset
data = []

np.random.seed(42)
for p in participants:
    for caf in caffeine_levels:
        for dist in distractions:
            mean = baseline_mean + caffeine_effect[caf] + distraction_effect[dist]
            value = max(120, np.random.normal(mean, baseline_sd))  # ensure realistic minimum
            data.append([p, caf, dist, round(value, 1)])

df = pd.DataFrame(data, columns=["participant", "caffeine_mg", "distraction", "reaction_time_ms"])

# Save CSV
csv_path = "/mnt/data/reaction_time_experiment.csv"
df.to_csv(csv_path, index=False)

csv_path, df.head()
