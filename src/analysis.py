"""Nusuk app users, 1447 AH: analysis by gender, quarter and (optionally) age group.

Run from the project root:  python src/analysis.py
Reads  data/raw/*.xlsx   ->  writes data/processed/*.csv, outputs/charts/*.png
"""
from pathlib import Path
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RAW, PROC, CHARTS = ROOT / "data/raw", ROOT / "data/processed", ROOT / "outputs/charts"
PROC.mkdir(parents=True, exist_ok=True)
CHARTS.mkdir(parents=True, exist_ok=True)

# Arabic month names -> English labels (charts avoid Arabic to dodge font/shaping issues)
MONTHS = {
    "ربيع الثاني": "Rabi II", "ربيع الآخر": "Rabi II",
    "جماد الأول": "Jumada I", "جمادى الأولى": "Jumada I",
    "جماد الثاني": "Jumada II", "جمادى الآخرة": "Jumada II",
    "رجب": "Rajab", "شعبان": "Shaban", "رمضان": "Ramadan",
    "شوال": "Shawwal", "ذو القعدة": "Dhu al-Qadah", "ذو الحجة": "Dhu al-Hijjah",
}
QUARTER_FILES = {"Q2": "users_q2_1447.xlsx", "Q3": "users_q3_1447.xlsx", "Q4": "users_q4_1447.xlsx"}


def read3(path):
    """Read a 3-column sheet by position (year, label, users) to be robust to header typos."""
    df = pd.read_excel(path).iloc[:, :3].dropna(how="all")
    df.columns = ["year", "label", "users"]
    df["label"] = df["label"].astype(str).str.strip()
    df["users"] = pd.to_numeric(df["users"])
    return df


def gender():
    df = read3(RAW / "users_by_gender_1447.xlsx")
    df["gender"] = df["label"].map({"ذكر": "Male", "أنثى": "Female"})
    df["share_pct"] = (df["users"] / df["users"].sum() * 100).round(2)
    out = df[["year", "gender", "users", "share_pct"]]
    out.to_csv(PROC / "users_by_gender.csv", index=False)
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(out["users"], labels=out["gender"], autopct="%1.1f%%", startangle=90,
           colors=["#1F4E78", "#9DC3E6"])
    ax.set_title("Nusuk users by gender, 1447 AH")
    fig.savefig(CHARTS / "users_by_gender.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def quarters():
    frames = []
    for q, fn in QUARTER_FILES.items():
        d = read3(RAW / fn)
        d["quarter"] = q
        d["month"] = d["label"].map(MONTHS)
        if d["month"].isna().any():
            sys.exit(f"Unmapped month name in {fn}: {d.loc[d['month'].isna(), 'label'].tolist()}")
        frames.append(d[["year", "quarter", "month", "users"]])
    monthly = pd.concat(frames, ignore_index=True)
    monthly["mom_change_pct"] = (monthly["users"].pct_change() * 100).round(1)
    monthly.to_csv(PROC / "users_by_month.csv", index=False)

    q = monthly.groupby("quarter", sort=True)["users"].sum().reset_index()
    q["share_pct"] = (q["users"] / q["users"].sum() * 100).round(1)
    q["qoq_change"] = q["users"].diff()
    q["qoq_change_pct"] = (q["users"].pct_change() * 100).round(1)
    q.to_csv(PROC / "users_by_quarter.csv", index=False)

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(q["quarter"], q["users"], color="#1F4E78")
    ax.bar_label(bars, labels=[f"{v:,.0f}" for v in q["users"]], padding=3)
    ax.set_title("Nusuk users by quarter, 1447 AH")
    ax.set_ylabel("Users"); ax.ticklabel_format(axis="y", style="plain")
    ax.set_ylim(0, q["users"].max() * 1.12)
    fig.savefig(CHARTS / "users_by_quarter.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4))
    colors = monthly["quarter"].map({"Q2": "#9DC3E6", "Q3": "#1F4E78", "Q4": "#2E75B6"})
    ax.bar(monthly["month"], monthly["users"], color=colors)
    ax.set_title("Nusuk users by month, 1447 AH (Q2-Q4)")
    ax.set_ylabel("Users"); ax.ticklabel_format(axis="y", style="plain")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.savefig(CHARTS / "users_by_month.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return monthly, q


def age_groups():
    """Optional: expects data/raw/users_by_age_group_1447.xlsx with columns year, age_group, users."""
    path = RAW / "users_by_age_group_1447.xlsx"
    if not path.exists():
        print("[skip] Age-group file not found: add data/raw/users_by_age_group_1447.xlsx")
        return None
    df = read3(path)
    if set(df["label"]) <= {"ذكر", "أنثى"}:
        print("[skip] Age-group file contains gender rows, not age groups. Replace it with the correct file.")
        return None
    df = df.rename(columns={"label": "age_group"})
    df["share_pct"] = (df["users"] / df["users"].sum() * 100).round(2)
    df.to_csv(PROC / "users_by_age_group.csv", index=False)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(df["age_group"], df["users"], color="#1F4E78")
    ax.set_title("Nusuk users by age group, 1447 AH")
    ax.set_ylabel("Users"); ax.ticklabel_format(axis="y", style="plain")
    fig.savefig(CHARTS / "users_by_age_group.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return df


def main():
    g = gender()
    monthly, q = quarters()
    age_groups()

    total_g, total_q = g["users"].sum(), q["users"].sum()
    print(f"Gender total:        {total_g:,}")
    print(f"Q2-Q4 total:         {total_q:,}")
    print(f"Gap (gender - Q2-Q4): {total_g - total_q:,}  <- check definitions / missing Q1")
    peak, low = monthly.loc[monthly["users"].idxmax()], monthly.loc[monthly["users"].idxmin()]
    print(f"Peak month: {peak['month']} ({peak['users']:,})   Lowest: {low['month']} ({low['users']:,})")
    print(q.to_string(index=False))


if __name__ == "__main__":
    main()
