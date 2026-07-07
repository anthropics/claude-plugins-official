# Türkiye — Search Provider

Bkz. sözleşme: [`core/engine/providers/search-provider.interface.md`](../../../core/engine/providers/search-provider.interface.md)

## search — bağlı kaynaklar

| Öncelik | Kaynak | Tier | Kapsam notu |
|---|---|---|---|
| 1 | Yargıtay Karar Arama (kamuya açık) | free | Yargıtay daire kararları, karar metni tam arama |
| 2 | Mevzuat Bilgi Sistemi (mevzuat.gov.tr) | free | Yürürlükteki kanun/yönetmelik/tebliğ metinleri |
| 3 | Resmî Gazete arşivi | free | Yayın tarihli resmî metin, yürürlük tarihi |
| 4 | Lexpera / Kazancı İçtihat Bilgi Bankası | paid | Kapsamlı içtihat + doktrin taraması, gelişmiş arama |

## preflightCheck — nasıl test edilir

Yargıtay Karar Arama'ya hafif bir sorgu (ör. yaygın bir hukuki terim) gönderilir; yapılandırılmış bir yanıt 2 saniye içinde dönerse `available: true`.

## getSourceCatalog

Yukarıdaki tablo, [`mcp-tool-registry.tr.yaml`](../mcp/mcp-tool-registry.tr.yaml)'daki `capability_id: case-law-search` girdileriyle eşleşir.

*Not: CourtListener/PACER'ın doğrudan TR karşılığı yoktur — Türkiye'de tek, birleşik bir yargı ağı (UYAP) mevcuttur; bu nedenle "federal vs. eyalet" ayrımı TR için geçerli değildir (bkz. `legal_family: civil_law`).*
