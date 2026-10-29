"""
Aralıklı talep denetimi — çekirdek yöntemler.
Veri: Monash Time Series Forecasting Archive, "Car Parts" (2674 aylık seri, 1998-01..2002-03),
R expsmooth paketinden türetilmiş. https://zenodo.org/records/3994911 (CC-BY 4.0)
"""
from __future__ import annotations
import numpy as np


# ---------------------------------------------------------------- veri okuma
def read_tsf(path: str) -> dict[str, np.ndarray]:
    """Monash .tsf/.ts dosyasını {seri_adı: değerler} olarak okur."""
    series: dict[str, np.ndarray] = {}
    in_data = False
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith("@data"):
                in_data = True
                continue
            if not in_data or line.startswith(("#", "@")):
                continue
            parts = line.split(":")
            if len(parts) < 3:
                continue
            name, vals = parts[0], parts[-1]
            series[name] = np.array([float(v) for v in vals.split(",")], dtype=float)
    return series


# ------------------------------------------------- sınıflandırma (ADI / CV^2)
def adi_cv2(x: np.ndarray) -> tuple[float, float]:
    """Ortalama talepler arası aralık (ADI) ve sıfır-dışı talebin kareli varyasyon katsayısı."""
    nz = x[x > 0]
    if nz.size == 0:
        return float("inf"), 0.0
    adi = len(x) / nz.size
    cv2 = (nz.std(ddof=0) / nz.mean()) ** 2 if nz.mean() > 0 else 0.0
    return float(adi), float(cv2)


def sbc_class(adi: float, cv2: float) -> str:
    """Syntetos-Boylan-Croston dörtlüsü. Eşikler: ADI=1.32, CV^2=0.49."""
    if adi == float("inf"):
        return "ölü (hiç hareket yok)"
    if adi < 1.32 and cv2 < 0.49:
        return "düzgün (smooth)"
    if adi < 1.32 and cv2 >= 0.49:
        return "düzensiz (erratic)"
    if adi >= 1.32 and cv2 < 0.49:
        return "aralıklı (intermittent)"
    return "yığınsal (lumpy)"


# ----------------------------------------------------------------- tahminler
def croston(x: np.ndarray, alpha: float = 0.1) -> float:
    """Klasik Croston (1972): talep büyüklüğü ve aralığı ayrı ayrı düzleştirilir."""
    nz_idx = np.flatnonzero(x > 0)
    if nz_idx.size == 0:
        return 0.0
    z = x[nz_idx[0]]                     # büyüklük
    p = float(nz_idx[0] + 1)             # aralık
    last = nz_idx[0]
    for i in nz_idx[1:]:
        z += alpha * (x[i] - z)
        p += alpha * ((i - last) - p)
        last = i
    return float(z / p) if p > 0 else 0.0


def sba(x: np.ndarray, alpha: float = 0.1) -> float:
    """Syntetos-Boylan yaklaşımı: Croston'un yapısal sapmasını (1 - alpha/2) ile düzeltir."""
    return (1.0 - alpha / 2.0) * croston(x, alpha)


def tsb(x: np.ndarray, alpha: float = 0.2, beta: float = 0.05) -> float:
    """Teunter-Syntetos-Babai: talep olasılığı her periyotta güncellenir (ölen parçayı yakalar)."""
    nz = x[x > 0]
    if nz.size == 0:
        return 0.0
    z = nz[0]
    p = nz.size / len(x)
    for v in x:
        occurred = 1.0 if v > 0 else 0.0
        p += beta * (occurred - p)
        if occurred:
            z += alpha * (v - z)
    return float(p * z)


def naive_mean(x: np.ndarray) -> float:
    """Taban çizgisi: tüm geçmişin ortalaması (ERP'lerin fiilen yaptığı şey)."""
    return float(x.mean()) if x.size else 0.0


def moving_average(x: np.ndarray, window: int = 12) -> float:
    return float(x[-window:].mean()) if x.size else 0.0


# ------------------------------------------------------------- değerlendirme
def mase(actual: np.ndarray, forecast: float, train: np.ndarray) -> float:
    """Ortalama ölçeklenmiş mutlak hata; ölçek = eğitim setinin naive-1 MAE'si."""
    scale = np.mean(np.abs(np.diff(train))) if train.size > 1 else 0.0
    if scale == 0:
        return float("nan")
    return float(np.mean(np.abs(actual - forecast)) / scale)


# ------------------------------------------- servis seviyesi <-> stok eğrisi
def fill_rate_and_stock(
    demand: np.ndarray, lead_time: int, order_up_to: float
) -> tuple[float, float]:
    """
    Periyodik gözden geçirmeli sipariş-noktası simülasyonu.
    Dönüş: (karşılama oranı, ortalama eldeki stok).
    """
    on_hand = order_up_to
    pipeline: list[float] = [0.0] * lead_time
    filled = total = 0.0
    hist = []
    for d in demand:
        arrived = pipeline.pop(0)
        on_hand += arrived
        served = min(on_hand, d)
        on_hand -= served
        filled += served
        total += d
        hist.append(on_hand)
        inv_position = on_hand + sum(pipeline)
        order = max(0.0, order_up_to - inv_position)
        pipeline.append(order)
    fill = (filled / total) if total > 0 else 1.0
    return float(fill), float(np.mean(hist))
