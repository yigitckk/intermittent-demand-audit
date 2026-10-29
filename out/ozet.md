# Denetim özeti (otomatik üretildi)

- Seri sayısı: **2674** parça, 51 ay (1998-01 → 2002-03)
- Ayların **%75.9**'i sıfır talep → klasik tahmin yöntemleri burada yanılıyor
- Sınıf dağılımı: aralıklı (intermittent) 2342, yığınsal (lumpy) 297, ölü (hiç hareket yok) 16, düzgün (smooth) 15, düzensiz (erratic) 4
- En iyi yöntem: **hareketli_ort12** (ortalama MASE 1.078)
- ERP'nin fiili davranışı (tüm geçmişin ortalaması) MASE 1.177
- **Kazanç: %8.4 daha düşük hata**
- ~%95 karşılama oranı için bağlanan sermaye: **59,387 €** (katsayı 2.5x)
- Son 12 ayda hiç hareket etmeyen ama geçmişte hareketli olan parça: **698** kalem (ölü stok adayı)

## Çıktı dosyaları
| Dosya | İçerik |
|---|---|
| 01_parca_siniflandirma.csv | Parça başına ADI, CV², sınıf, tahminler, MASE |
| 02_yontem_karsilastirma.csv | Yöntemlerin ortalama/medyan MASE'si |
| 03_sinif_bazli_mase.csv | Hangi sınıfta hangi yöntem kazanıyor |
| 04_servis_stok_egrisi.csv | Karşılama oranı ↔ bağlanan sermaye |
| 05_olu_stok_adaylari.csv | Nakde çevrilebilir kalemler |
| 06_siparis_noktasi_tablosu.csv | ERP'ye girilebilir sipariş noktası / üst seviye |
