import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("/Users/apple/Downloads/Covid Data.csv", low_memory=False)
rows_before = len(df)

# ---------- CLEANING ----------
df.columns = df.columns.str.strip().str.lower()
df = df.rename(columns={"clasification_final": "classification_final",
                        "clasiffication_final": "classification_final"})
print(df.columns.tolist())
df = df.drop_duplicates()

yes_no = ["intubed", "pneumonia", "pregnant", "icu", "diabetes", "copd", "asthma",
          "inmsupr", "hipertension", "other_disease", "cardiovascular",
          "obesity", "renal_chronic", "tobacco"]

# 97, 98, 99 = missing, phir 1 = Yes, 2 = No
for col in yes_no:
    df[col] = df[col].replace([97, 98, 99], pd.NA).map({1: "Yes", 2: "No"})

df["sex"] = df["sex"].map({1: "Female", 2: "Male"})
df["patient_type"] = df["patient_type"].map({1: "Outpatient", 2: "Hospitalized"})

# Maut: 9999-99-99 = zinda
df["died"] = df["date_died"] != "9999-99-99"
df["date_died"] = pd.to_datetime(df["date_died"], errors="coerce", dayfirst=True)

# Ghalat umar hatao
df = df[(df["age"] >= 0) & (df["age"] <= 110)]

# Confirmed = classification 1 se 3
df["confirmed"] = df["classification_final"] <= 3
df["recovered"] = df["confirmed"] & ~df["died"]
df["age_group"] = pd.cut(df["age"], bins=[0, 17, 34, 49, 64, 79, 110],
                         labels=["0-17", "18-34", "35-49", "50-64", "65-79", "80+"],
                         include_lowest=True)

print("Rows pehle:", rows_before, "| baad mein:", len(df))
print("\nMissing values:\n", df.isnull().sum())
df.to_csv("/Users/apple/Downloads/clean_covid_patients.csv", index=False)

# ---------- ANALYSIS ----------
conf = df[df["confirmed"]]
confirmed = len(conf)
deaths = int(conf["died"].sum())
recovered = int(df["recovered"].sum())
conditions = ["diabetes", "hipertension", "obesity", "pneumonia", "copd", "cardiovascular", "renal_chronic"]

print("\n===== KEY NUMBERS =====")
print("Total patients:", len(df))
print("Confirmed:", confirmed)
print("Deaths (confirmed mein se):", deaths)
print("Recovered (confirmed aur zinda):", recovered)
print("Death rate: %.2f%%" % (deaths / confirmed * 100))
print("Average age zinda: %.1f | faut: %.1f" % (conf[~conf["died"]]["age"].mean(), conf[conf["died"]]["age"].mean()))
print("\nDeath rate by age group (%):")
print((conf.groupby("age_group", observed=True)["died"].mean() * 100).round(2))
print("\nDeath rate by sex (%):")
print((conf.groupby("sex")["died"].mean() * 100).round(2))
print("\nDeath rate by bimari (%):")
for c in conditions:
    print(c, round(conf[conf[c] == "Yes"]["died"].mean() * 100, 2))

# ---------- GRAPHS ----------
fig, ax = plt.subplots(2, 2, figsize=(16, 10))
fig.suptitle("COVID-19 Patient Data EDA", fontsize=20, fontweight="bold")

# 1. Confirmed, Recovered, Deaths
bars = ax[0, 0].bar(["Confirmed", "Recovered", "Deaths"], [confirmed, recovered, deaths],
                    color=["#2563eb", "#16a34a", "#ef4444"])
ax[0, 0].bar_label(bars)
ax[0, 0].set_title("Confirmed vs Recovered vs Deaths", fontweight="bold")

# 2. Age group ke hisaab se death rate
agr = conf.groupby("age_group", observed=True)["died"].mean() * 100
b2 = ax[0, 1].bar(agr.index.astype(str), agr.values, color="#f59e0b")
ax[0, 1].bar_label(b2, fmt="%.1f%%")
ax[0, 1].set_title("Death Rate by Age Group", fontweight="bold")
ax[0, 1].set_ylabel("Death rate (%)")


cs = pd.Series({c: conf[conf[c] == "Yes"]["died"].mean() * 100 for c in conditions}).sort_values()
ax[1, 0].barh(cs.index, cs.values, color="#ef4444")
ax[1, 0].set_title("Death Rate by Pre-existing Condition", fontweight="bold")
ax[1, 0].set_xlabel("Death rate (%)")


monthly = conf[conf["died"]].groupby(conf["date_died"].dt.to_period("M")).size()
ax[1, 1].plot(monthly.index.astype(str), monthly.values, marker="o", color="#ef4444", linewidth=2)
ax[1, 1].set_title("Deaths per Month", fontweight="bold")
ax[1, 1].tick_params(axis="x", rotation=45)
ax[1, 1].grid(True, linestyle="--", alpha=0.4)

plt.tight_layout()
plt.savefig("/Users/apple/Downloads/covid_eda.png", dpi=150)
plt.show()