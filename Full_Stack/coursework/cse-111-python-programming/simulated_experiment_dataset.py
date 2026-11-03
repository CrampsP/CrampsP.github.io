# Creating a simulated experiment dataset (20 fictional students), saving as CSV, and showing a quick t-test.
import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

names = [
    "Alex Morgan","Bella Smith","Carlos Diaz","Diana Lee","Ethan Brown","Fiona Davis",
    "George Clark","Hannah Wilson","Ian Thompson","Julia Martinez","Kevin Johnson",
    "Lily Walker","Marcus Hall","Nora Allen","Omar King","Paula Scott",
    "Quentin Young","Rosa Hernandez","Samuel Rivera","Tina Nguyen"
]

# Randomize order and assign to two groups (10 each)
shuffled = names.copy()
np.random.shuffle(shuffled)
group_assignment = ["More Homework (+2h)"]*10 + ["Less Homework (-2h)"]*10
# ensure random pairing by shuffling group labels too
np.random.shuffle(group_assignment)

# Simulate exam scores (40-point exam)
# We'll simulate a modest treatment effect: More Homework -> slightly higher mean score.
scores = []
for g in group_assignment:
    if g == "More Homework (+2h)":
        s = np.random.normal(loc=29, scale=4.5)  # mean ~29/40
    else:
        s = np.random.normal(loc=25, scale=5.0)  # mean ~25/40
    # clamp between 0 and 40 and round to nearest integer
    s = int(np.clip(round(s), 0, 40))
    scores.append(s)

df = pd.DataFrame({
    "student_name": shuffled,
    "treatment_group": group_assignment,
    "final_score_40pt": scores
})

# Quick t-test and effect size (Cohen's d)
def cohens_d(x, y):
    nx, ny = len(x), len(y)
    dof = nx + ny - 2
    pooled_sd = np.sqrt(((nx - 1)*np.var(x, ddof=1) + (ny - 1)*np.var(y, ddof=1)) / dof)
    return (np.mean(x) - np.mean(y)) / pooled_sd

more_scores = df.loc[df['treatment_group']=="More Homework (+2h)", 'final_score_40pt'].values
less_scores = df.loc[df['treatment_group']=="Less Homework (-2h)", 'final_score_40pt'].values

# Try using scipy for t-test; fallback to manual if not installed
try:
    from scipy.stats import ttest_ind
    t_stat, p_val = ttest_ind(more_scores, less_scores, equal_var=False)
except Exception as e:
    # Welch's t-test manual calculation
    m1, m2 = np.mean(more_scores), np.mean(less_scores)
    s1, s2 = np.var(more_scores, ddof=1), np.var(less_scores, ddof=1)
    n1, n2 = len(more_scores), len(less_scores)
    t_stat = (m1 - m2) / np.sqrt(s1/n1 + s2/n2)
    # degrees of freedom for Welch's t-test
    df_welch = (s1/n1 + s2/n2)**2 / ((s1**2)/((n1**2)*(n1-1)) + (s2**2)/((n2**2)*(n2-1)))
    # approximate p-value using survival function from t distribution
    try:
        from scipy.stats import t as tdist
        p_val = 2 * tdist.sf(abs(t_stat), df_welch)
    except Exception:
        p_val = np.nan

cohens = cohens_d(more_scores, less_scores)

# Save CSV to current working directory (cross-platform)
out_path = Path.cwd() / "students_scores.csv"
df.to_csv(out_path, index=False)

# Display results
print("Dataset saved to:", out_path)
print("\nGroup means and counts:")
print(df.groupby('treatment_group')['final_score_40pt'].agg(['mean','count','std']).round(2))
print(f"\nWelch t-statistic = {t_stat:.3f}, p-value = {p_val:.4f}")
print(f"Cohen's d (pooled) = {cohens:.3f}")

# Try to show the DataFrame with caas_jupyter_tools when available;
# otherwise fall back to printing the DataFrame to the console.
try:
    import caas_jupyter_tools as cjt
    cjt.display_dataframe_to_user("Simulated Student Scores", df)
except Exception:
    print("\n(caas_jupyter_tools not available; printing DataFrame instead.)")
    # Print a full table but without the index for readability
    print(df.to_string(index=False))

# End of script — the dataframe `df` is available in this module if imported.

