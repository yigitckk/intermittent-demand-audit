"""
Denetim koşucusu: sınıflandırma + tahmin karşılaştırması + servis/stok eğrisi + ölü stok.
Çıktılar: out/*.csv, out/*.png, out/ozet.md
"""
from __future__ import annotations
import os
import sys
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from methods import (  # noqa: E402
    read_tsf, adi_cv2, sbc_class, croston, sba, tsb, naive_mean,
    moving_average, mase, fill_rate_and_stock,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "car_parts_dataset_without_missing_values.ts")
OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)

HOLDOUT = 12          # son 12 ay test
LEAD_TIME = 2         # ay
UNIT_COST = 40.0      # EUR/parça (örnek; müşteri verisinde gerçek maliyet gelir)


def main() -> None:
    series = read_tsf(DATA)
    print(f"{len(series)} seri okundu, uzunluk {len(next(iter(series.values())))} ay")

    rows = []
    for name, x in series.items():
        train, test = x[:-HOLDOUT], x[-HOLDOUT:]
        adi, cv2 = adi_cv2(train)
        f = {
            "naive_ortalama": naive_mean(train),
            "hareketli_ort12": moving_average(train, 12),
            "croston": croston(train),
            "sba": sba(train),
            "tsb": tsb(train),
        }
        row = {
            "parca": name,
            "adi": adi,
            "cv2": cv2,
            "sinif": sbc_class(adi, cv2),
            "sifir_ay_orani": float((x == 0).mean()),
            "yillik_talep": float(x.sum() / (len(x) / 12)),
            "son12ay_hareket": float(x[-12:].sum()),
        }
        for k, v in f.items():
            row[f"tahmin_{k}"] = v
            row[f"mase_{k}"] = mase(test, v, train)
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "01_parca_siniflandirma.csv"), index=False)

    # ---------------------------------------------------------- 1) sınıf dağılımı
    dist = df["sinif"].value_counts()
    print("\nSınıf dağılımı:\n", dist.to_string())

    # ---------------------------------------------- 2) yöntem karşılaştırma (MASE)
    methods = ["naive_ortalama", "hareketli_ort12", "croston", "sba", "tsb"]
    comp = pd.DataFrame(
        {
            "yontem": methods,
            "mase_ortalama": [df[f"mase_{m}"].mean(skipna=True) for m in methods],
            "mase_medyan": [df[f"mase_{m}"].median(skipna=True) for m in methods],
        }
    ).sort_values("mase_ortalama")
    comp.to_csv(os.path.join(OUT, "02_yontem_karsilastirma.csv"), index=False)
    print("\nYöntem karşılaştırması (düşük = iyi):\n", comp.to_string(index=False))

    # sınıf bazlı kazanç
    by_class = df.groupby("sinif")[[f"mase_{m}" for m in methods]].mean()
    by_class.to_csv(os.path.join(OUT, "03_sinif_bazli_mase.csv"))

    # ---------------------------------------------- 3) servis seviyesi <-> stok eğrisi
    best = comp.iloc[0]["yontem"]
    # en çok hareket eden 200 parçayla eğri (hesap süresi için)
    top = df.nlargest(200, "yillik_talep")["parca"].tolist()
    curve = []
    for mult in [0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]:
        fills, stocks, values = [], [], []
        for name in top:
            x = series[name]
            mu = df.loc[df["parca"] == name, f"tahmin_{best}"].iloc[0]
            oup = mu * (LEAD_TIME + 1) * mult
            fr, avg = fill_rate_and_stock(x[-24:], LEAD_TIME, oup)
            fills.append(fr)
            stocks.append(avg)
            values.append(avg * UNIT_COST)
        curve.append(
            {
                "katsayi": mult,
                "karsilama_orani": float(np.mean(fills)),
                "ortalama_stok_adet": float(np.sum(stocks)),
                "baglanan_sermaye_eur": float(np.sum(values)),
            }
        )
    cdf = pd.DataFrame(curve)
    cdf.to_csv(os.path.join(OUT, "04_servis_stok_egrisi.csv"), index=False)
    print("\nServis seviyesi / sermaye eğrisi (en hareketli 200 parça):\n", cdf.to_string(index=False))

    # ---------------------------------------------------------------- 4) ölü stok
    dead = df[(df["son12ay_hareket"] == 0) & (df["yillik_talep"] > 0)].copy()
    dead = dead.sort_values("yillik_talep", ascending=False)
    dead[["parca", "yillik_talep", "sifir_ay_orani", "sinif"]].to_csv(
        os.path.join(OUT, "05_olu_stok_adaylari.csv"), index=False
    )

    # --------------------------------------------- 5) sipariş noktası tablosu (ERP'ye)
    z = 1.65  # ~%95 servis
    rp = df[["parca", "sinif", f"tahmin_{best}"]].copy()
    rp.columns = ["parca", "sinif", "aylik_tahmin"]
    sigma = []
    for name in df["parca"]:
        x = series[name][:-HOLDOUT]
        sigma.append(float(x.std(ddof=0)))
    rp["aylik_std"] = sigma
    rp["tedarik_suresi_ay"] = LEAD_TIME
    rp["emniyet_stogu"] = (z * rp["aylik_std"] * np.sqrt(LEAD_TIME)).round(2)
    rp["siparis_noktasi"] = (rp["aylik_tahmin"] * LEAD_TIME + rp["emniyet_stogu"]).round(2)
    rp["siparis_ustu_seviye"] = (rp["aylik_tahmin"] * (LEAD_TIME + 1) + rp["emniyet_stogu"]).round(2)
    rp.to_csv(os.path.join(OUT, "06_siparis_noktasi_tablosu.csv"), index=False)

    # ------------------------------------------------------------------- grafikler
    fig, ax = plt.subplots(figsize=(7, 5))
    sub = df[np.isfinite(df["adi"])]
    colors = {
        "düzgün (smooth)": "#2a9d8f",
        "düzensiz (erratic)": "#e9c46a",
        "aralıklı (intermittent)": "#457b9d",
        "yığınsal (lumpy)": "#e76f51",
    }
    for k, g in sub.groupby("sinif"):
        ax.scatter(g["adi"], g["cv2"], s=6, alpha=0.5, label=f"{k} ({len(g)})",
                   color=colors.get(k, "#888"))
    ax.axvline(1.32, color="k", lw=0.8, ls="--")
    ax.axhline(0.49, color="k", lw=0.8, ls="--")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("ADI — ortalama talepler arası aralık (ay)")
    ax.set_ylabel("CV² — sıfır-dışı talep değişkenliği")
    ax.set_title("Parça sınıflandırması (Syntetos-Boylan-Croston)")
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "grafik_01_siniflandirma.png"), dpi=140)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(comp["yontem"], comp["mase_ortalama"], color="#457b9d")
    ax.set_xlabel("Ortalama MASE (düşük = iyi)")
    ax.set_title(f"Yöntem karşılaştırması — {len(df)} parça, son {HOLDOUT} ay test")
    for i, (m, v) in enumerate(zip(comp["yontem"], comp["mase_ortalama"])):
        ax.text(v, i, f" {v:.3f}", va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "grafik_02_yontem_mase.png"), dpi=140)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(cdf["baglanan_sermaye_eur"], cdf["karsilama_orani"] * 100, "o-", color="#e76f51")
    for _, r in cdf.iterrows():
        ax.annotate(f"{r['katsayi']:g}x", (r["baglanan_sermaye_eur"], r["karsilama_orani"] * 100),
                    textcoords="offset points", xytext=(4, -9), fontsize=7)
    ax.set_xlabel(f"Bağlanan sermaye (EUR, parça başı {UNIT_COST:.0f}€ varsayımı)")
    ax.set_ylabel("Karşılama oranı (%)")
    ax.set_title("Servis seviyesi ↔ sermaye eğrisi (en hareketli 200 parça)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "grafik_03_servis_sermaye.png"), dpi=140)

    # --------------------------------------------------------------------- özet
    best_row = comp.iloc[0]
    naive_row = comp[comp["yontem"] == "naive_ortalama"].iloc[0]
    gain = (naive_row["mase_ortalama"] - best_row["mase_ortalama"]) / naive_row["mase_ortalama"] * 100
    knee = cdf.iloc[(cdf["karsilama_orani"] - 0.95).abs().argsort()].iloc[0]
    with open(os.path.join(OUT, "ozet.md"), "w", encoding="utf-8") as fh:
        fh.write(f"""# Denetim özeti (otomatik üretildi)

- Seri sayısı: **{len(df)}** parça, {len(next(iter(series.values())))} ay (1998-01 → 2002-03)
- Ayların **%{df['sifir_ay_orani'].mean()*100:.1f}**'i sıfır talep → klasik tahmin yöntemleri burada yanılıyor
- Sınıf dağılımı: {", ".join(f"{k} {v}" for k, v in dist.items())}
- En iyi yöntem: **{best_row['yontem']}** (ortalama MASE {best_row['mase_ortalama']:.3f})
- ERP'nin fiili davranışı (tüm geçmişin ortalaması) MASE {naive_row['mase_ortalama']:.3f}
- **Kazanç: %{gain:.1f} daha düşük hata**
- ~%95 karşılama oranı için bağlanan sermaye: **{knee['baglanan_sermaye_eur']:,.0f} €** (katsayı {knee['katsayi']:g}x)
- Son 12 ayda hiç hareket etmeyen ama geçmişte hareketli olan parça: **{len(dead)}** kalem (ölü stok adayı)

## Çıktı dosyaları
| Dosya | İçerik |
|---|---|
| 01_parca_siniflandirma.csv | Parça başına ADI, CV², sınıf, tahminler, MASE |
| 02_yontem_karsilastirma.csv | Yöntemlerin ortalama/medyan MASE'si |
| 03_sinif_bazli_mase.csv | Hangi sınıfta hangi yöntem kazanıyor |
| 04_servis_stok_egrisi.csv | Karşılama oranı ↔ bağlanan sermaye |
| 05_olu_stok_adaylari.csv | Nakde çevrilebilir kalemler |
| 06_siparis_noktasi_tablosu.csv | ERP'ye girilebilir sipariş noktası / üst seviye |
""")
    print("\n✓ out/ klasörüne yazıldı")


if __name__ == "__main__":
    main()
