"""Grafiklerin İngilizce sürümü (blog + müşteriye giden PDF için).
Türkçe sürümler out/grafik_*.png olarak kalır; bunlar out/chart_*_en.png olur.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")

LABELS = {
    "düzgün (smooth)": "smooth",
    "düzensiz (erratic)": "erratic",
    "aralıklı (intermittent)": "intermittent",
    "yığınsal (lumpy)": "lumpy",
    "ölü (hiç hareket yok)": "dead (no movement)",
}
COLORS = {
    "smooth": "#2a9d8f",
    "erratic": "#e9c46a",
    "intermittent": "#457b9d",
    "lumpy": "#e76f51",
    "dead (no movement)": "#888888",
}
METHOD_EN = {
    "secilen": "per-part selection",
    "hareketli_ort12": "moving average (12m)",
    "hareketli_ort6": "moving average (6m)",
    "tsb_a0.2_b0.05": "TSB",
    "naive_ortalama": "naive mean (ERP-style)",
    "sba_a0.1": "SBA",
    "croston_a0.1": "Croston",
}


def classification() -> None:
    df = pd.read_csv(os.path.join(OUT, "01_parca_siniflandirma.csv"))
    df["cls"] = df["sinif"].map(LABELS).fillna(df["sinif"])
    sub = df[np.isfinite(df["adi"])]
    fig, ax = plt.subplots(figsize=(7, 5))
    for k, g in sub.groupby("cls"):
        ax.scatter(g["adi"], g["cv2"], s=6, alpha=0.5, label=f"{k} ({len(g)})",
                   color=COLORS.get(k, "#888"))
    ax.axvline(1.32, color="k", lw=0.8, ls="--")
    ax.axhline(0.49, color="k", lw=0.8, ls="--")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("ADI — average inter-demand interval (months)")
    ax.set_ylabel("CV² — variability of non-zero demand")
    ax.set_title("Part classification (Syntetos-Boylan-Croston)")
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "chart_classification_en.png"), dpi=140)


def methods() -> None:
    df = pd.read_csv(os.path.join(OUT, "08_secim_sonrasi_karsilastirma.csv"))
    df["label"] = df["yaklasim"].map(METHOD_EN).fillna(df["yaklasim"])
    df = df.sort_values("test_mase_ortalama", ascending=False)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = ["#c1440e" if y == "secilen" else "#457b9d" for y in df["yaklasim"]]
    ax.barh(df["label"], df["test_mase_ortalama"], color=colors)
    ax.set_xlabel("Mean MASE on the held-out test window (lower is better)")
    ax.set_title("Method comparison — 2,674 parts, final 12 months unseen")
    for i, v in enumerate(df["test_mase_ortalama"]):
        ax.text(v, i, f" {v:.3f}", va="center", fontsize=8)
    ax.set_xlim(0, max(df["test_mase_ortalama"]) * 1.15)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "chart_methods_en.png"), dpi=140)


def service_curve() -> None:
    cdf = pd.read_csv(os.path.join(OUT, "04_servis_stok_egrisi.csv"))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(cdf["baglanan_sermaye_eur"], cdf["karsilama_orani"] * 100, "o-", color="#c1440e")
    ax.set_xlabel("Capital tied up in stock (EUR, at €40 per part)")
    ax.set_ylabel("Fill rate (%)")
    ax.set_title("Service level vs tied-up capital (200 fastest-moving parts)")
    ax.grid(alpha=0.3)
    for pct, txt in [(95, "95%"), (99, "99%")]:
        row = cdf.iloc[(cdf["karsilama_orani"] - pct / 100).abs().argsort()].iloc[0]
        ax.annotate(f"{txt} → €{row['baglanan_sermaye_eur']:,.0f}",
                    (row["baglanan_sermaye_eur"], row["karsilama_orani"] * 100),
                    textcoords="offset points", xytext=(8, -12), fontsize=8.5,
                    color="#1d2731")
        ax.scatter([row["baglanan_sermaye_eur"]], [row["karsilama_orani"] * 100],
                   s=60, facecolors="none", edgecolors="#1d2731", zorder=5)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "chart_service_capital_en.png"), dpi=140)


if __name__ == "__main__":
    classification()
    methods()
    service_curve()
    print("ingilizce grafikler yazildi: out/chart_*_en.png")
