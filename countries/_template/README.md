# `_template/` — Yeni Ülke Plugin'i İskeleti

Bu dizin **kurulabilir bir plugin değildir** — yeni bir ülke eklerken kopyalanacak referans iskelettir. Kullanım için bkz. [`countries/README.md`](../README.md) → "Yeni bir ülke eklemek".

## Bu iskelet neyi garanti eder

- Her dosya, karşılık gelen `core/` şemasına/arayüzüne açık bir yorum satırıyla bağlıdır — bir katkı sağlayıcı hangi şemaya uyması gerektiğini asla tahmin etmek zorunda kalmaz.
- Her alan `[PLACEHOLDER]` ile işaretlenmiştir — bu, `scripts/lint-country-plugin.py` (sonraki dalga) tarafından "hâlâ şablon, henüz doldurulmamış" olarak tespit edilebilir bir kalıptır (reponun mevcut `[PLACEHOLDER]` tespiti + cold-start-interview yönlendirme desenine paralel).
- Hiçbir alan önceden bir ülkeye özgü örnek değerle doldurulmamıştır — bu, şablonun kazara "varsayılan ülke" varsayımı taşımamasını garanti eder.
