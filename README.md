# Aralıklı Talep Denetimi — yedek parça stok politikası

> Yılda iki kez hareket eden bir parçayı "ortalama tüketim" mantığıyla planlarsanız, aynı anda hem ölü stok hem stok-dışı kalma üretirsiniz. Bu repo o iddiayı **açık veriyle ölçer**: parçaları sınıflandırır, yöntem seçimini parça bazında yapar, ve kararı "servis seviyesi ↔ bağlanan sermaye" eğrisine indirir.

Türkçe teknik not + çalışan kod. Müşteri verisi içermez.

## Problem

Yedek parça / MRO deposunda talep **aralıklıdır**: çoğu ay sıfır, hareket olduğunda miktar değişkendir. ERP'lerin min/max alanları ve klasik tahmin yöntemleri bu yapıyı varsayımsal olarak ihlal eder. Sonuç depo müdürünün cümlesiyle: *"raf dolu ama aradığımız parça yok."*

Kullanılan veri: **Monash Time Series Forecasting Archive — Car Parts**, 2674 aylık seri, Ocak 1998 – Mart 2002 (R `expsmooth` paketinden türetilmiş, CC-BY 4.0).
Kaynak: https://zenodo.org/records/3994911 · Hyndman (2015), `expsmooth` R paketi.

Veri ne kadar aralıklı: **ayların %75,9'u sıfır talep.**

## Yöntem

1. **Sınıflandırma (Syntetos-Boylan-Croston):** her parça ADI (ortalama talepler arası aralık) ve CV² (sıfır-dışı talep değişkenliği) eksenine oturtulur; eşikler ADI = 1,32 ve CV² = 0,49.
2. **Tahmin adayları:** Croston (1972), SBA (Syntetos-Boylan düzeltmesi, `1 − α/2`), TSB (Teunter-Syntetos-Babai — talep olasılığını her periyot güncellediği için ölen parçayı yakalar), hareketli ortalama (6/12 ay) ve naive ortalama (ERP'nin fiili davranışı).
3. **Dürüst değerlendirme:** `α` ve yöntem **doğrulama penceresinde** (son 24 ayın ilk 12'si) parça bazında seçilir, skor **hiç görülmemiş** son 12 ayda ölçülür. Metrik: MASE (ölçek = eğitim setinin naive-1 MAE'si).
4. **Envanter simülasyonu:** periyodik gözden geçirmeli sipariş-üstü-seviye politikası, 2 ay tedarik süresi; çıktı karşılama oranı ve ortalama eldeki stok.

## Sonuçlar (kodun ürettiği gerçek sayılar)

Sınıf dağılımı — portföyün neredeyse tamamı klasik yöntemlerin varsayımını ihlal ediyor:

| Sınıf | Parça |
|---|---|
| aralıklı (intermittent) | 2342 |
| yığınsal (lumpy) | 297 |
| ölü (hiç hareket yok) | 16 |
| düzgün (smooth) | 15 |
| düzensiz (erratic) | 4 |

Test penceresi (hiç görülmemiş son 12 ay), düşük = iyi:

| Yaklaşım | Ortalama MASE | Medyan MASE |
|---|---|---|
| **parça bazında seçim** | **0,892** | **0,633** |
| hareketli ortalama (12 ay) | 0,922 | 0,671 |
| TSB (α=0,2, β=0,05) | 1,001 | 0,719 |
| naive ortalama (ERP tarzı) | 1,070 | 0,802 |
| SBA (α=0,1) | 1,313 | 0,913 |
| Croston (α=0,1) | 1,349 | 0,938 |

**ERP tarzı naive ortalamaya göre %16,6 daha düşük hata.**

Doğrulamada parça başına seçilen yöntem aileleri: hareketli ortalama 6 ay → 1147, SBA → 758, hareketli ortalama 12 ay → 248, TSB → 163, naive → 144, Croston → 44.

### Dürüst bulgu

**Tek bir yöntemi tüm portföye dayatmak kaybediyor.** Croston ve SBA sabit α ile naive ortalamanın *altında* kaldı; kazanan şey yöntemin kendisi değil, **parça bazında seçim disiplini** oldu (ve seçim 758 parçada gerçekten SBA'yı seçti). Literatürdeki "Croston her zaman kazanır" beklentisi bu veride doğrulanmıyor — bu yüzden denetim, yöntem satmak yerine ölçüm satar.

### Servis seviyesi ↔ bağlanan sermaye

En hareketli 200 parça, parça başı 40 € varsayımıyla:

| Karşılama oranı | Bağlanan sermaye |
|---|---|
| %72 | 17.700 € |
| %86 | 30.600 € |
| %92 | 44.600 € |
| **%95** | **59.400 €** |
| %97 | 74.300 € |
| %98 | 104.600 € |
| %99 | 288.000 € |

Eğrinin dizi noktası burada: **%95 → %99 arasında sermaye 5 katına çıkıyor.** Karar kuruluna götürülecek cümle budur, "optimal stok" değil.

Ayrıca: son 12 ayda hiç hareket etmeyen ama geçmişte hareketli **698 kalem** ölü stok adayı olarak listelenir.

## Çıktılar

`out/` klasörü (kod çalıştırılınca üretilir):

| Dosya | İçerik |
|---|---|
| `01_parca_siniflandirma.csv` | Parça başına ADI, CV², sınıf, tahminler, MASE |
| `02_yontem_karsilastirma.csv` | Yöntemlerin ortalama/medyan MASE'si |
| `03_sinif_bazli_mase.csv` | Hangi sınıfta hangi yöntem kazanıyor |
| `04_servis_stok_egrisi.csv` | Karşılama oranı ↔ bağlanan sermaye |
| `05_olu_stok_adaylari.csv` | Nakde çevrilebilir kalemler |
| `06_siparis_noktasi_tablosu.csv` | ERP'ye girilebilir sipariş noktası / üst seviye |
| `07_yontem_secimi.csv` | Parça başına seçilen yöntem |
| `08_secim_sonrasi_karsilastirma.csv` | Test penceresi karşılaştırması |
| `grafik_01_siniflandirma.png` | ADI–CV² saçılımı |
| `grafik_02_yontem_mase.png` | Yöntem karşılaştırma çubukları |
| `grafik_03_servis_sermaye.png` | Servis ↔ sermaye eğrisi |

## Çalıştırma

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python pandas numpy matplotlib

# veri (2674 seri, ~40 KB zip)
curl -sL -o data/car_parts.zip \
  "https://zenodo.org/records/3994911/files/car_parts_dataset_without_missing_values.zip?download=1"
cd data && unzip -o car_parts.zip && cd ..

.venv/bin/python src/audit.py           # sınıflandırma + eğri + tablolar (~8 sn)
.venv/bin/python src/select_method.py   # dürüst yöntem seçimi + test skoru (~4 sn)
```

## Kendi verinizle

`src/methods.py` içindeki `read_tsf` yerine ERP dökümünüzü okuyun; gereken kolonlar: parça kodu, tarih, hareket miktarı (opsiyonel: birim maliyet, tedarik süresi). Sensör, PLC, entegrasyon gerekmez.

## Kaynaklar

- Croston, J.D. (1972). *Forecasting and stock control for intermittent demands.* Operational Research Quarterly 23(3).
- Syntetos, A.A., Boylan, J.E. (2005). *The accuracy of intermittent demand estimates.* International Journal of Forecasting 21(2).
- Teunter, R.H., Syntetos, A.A., Babai, M.Z. (2011). *Intermittent demand: Linking forecasting to inventory obsolescence.* European Journal of Operational Research 214(3).
- Hyndman, R.J., Koehler, A.B. (2006). *Another look at measures of forecast accuracy.* International Journal of Forecasting 22(4). (MASE)
- Godahewa, R. ve ark. (2021). *Monash Time Series Forecasting Archive.* NeurIPS Datasets and Benchmarks.

## Lisans

Kod: MIT. Veri: CC-BY 4.0 (Monash archive / `expsmooth`), repoda yeniden dağıtılmaz — kurulum adımında indirilir.
