"""
Yöntem seçimi, dürüst hâliyle: her parça için alfa ve yöntem bir DOĞRULAMA penceresinde
seçilir, sonra hiç görülmemiş test penceresinde ölçülür. Sonucu önceden varsaymıyoruz.
"""
from __future__ import annotations
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from methods import read_tsf, croston, sba, tsb, naive_mean, moving_average, mase  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "car_parts_dataset_without_missing_values.ts")
OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)

TEST = 12
VALID = 12
ALPHAS = [0.05, 0.1, 0.2, 0.3]


def candidates(x: np.ndarray) -> dict[str, float]:
    c: dict[str, float] = {
        "naive_ortalama": naive_mean(x),
        "hareketli_ort6": moving_average(x, 6),
        "hareketli_ort12": moving_average(x, 12),
    }
    for a in ALPHAS:
        c[f"croston_a{a}"] = croston(x, a)
        c[f"sba_a{a}"] = sba(x, a)
    for a in [0.1, 0.2, 0.3]:
        for b in [0.02, 0.05, 0.1]:
            c[f"tsb_a{a}_b{b}"] = tsb(x, a, b)
    return c


def main() -> None:
    series = read_tsf(DATA)
    fit_end = -(TEST + VALID)

    rows = []
    for name, x in series.items():
        fit, valid, test = x[:fit_end], x[fit_end:-TEST], x[-TEST:]
        if fit.size < 12:
            continue
        cands = candidates(fit)
        # doğrulama penceresinde seç
        vscores = {k: mase(valid, v, fit) for k, v in cands.items()}
        vscores = {k: v for k, v in vscores.items() if np.isfinite(v)}
        if not vscores:
            continue
        chosen = min(vscores, key=vscores.get)
        family = chosen.split("_a")[0]

        # seçilen yöntemi tüm eğitim verisiyle (fit+valid) yeniden kur, test penceresinde ölç
        train = x[:-TEST]
        cands_full = candidates(train)
        row = {"parca": name, "secilen": chosen, "aile": family,
               "mase_secilen": mase(test, cands_full[chosen], train)}
        # sabit alternatiflerin test skoru (karşılaştırma için)
        for k in ["naive_ortalama", "hareketli_ort12", "croston_a0.1", "sba_a0.1", "tsb_a0.2_b0.05"]:
            row[f"mase_{k}"] = mase(test, cands_full[k], train)
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "07_yontem_secimi.csv"), index=False)

    cols = [c for c in df.columns if c.startswith("mase_")]
    summary = (
        pd.DataFrame({
            "yaklasim": [c.replace("mase_", "") for c in cols],
            "test_mase_ortalama": [df[c].mean(skipna=True) for c in cols],
            "test_mase_medyan": [df[c].median(skipna=True) for c in cols],
        })
        .sort_values("test_mase_ortalama")
    )
    summary.to_csv(os.path.join(OUT, "08_secim_sonrasi_karsilastirma.csv"), index=False)

    print("Parça başına doğrulamada seçilen yöntem aileleri:")
    print(df["aile"].value_counts().to_string())
    print("\nTEST penceresi sonuçları (düşük = iyi):")
    print(summary.to_string(index=False))

    base = summary[summary["yaklasim"] == "naive_ortalama"]["test_mase_ortalama"].iloc[0]
    best = summary.iloc[0]
    print(f"\nERP tarzı naive ortalamaya göre kazanç: %{(base - best['test_mase_ortalama']) / base * 100:.1f} "
          f"({best['yaklasim']})")


if __name__ == "__main__":
    main()
