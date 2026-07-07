# United States — Search Provider

Bkz. sözleşme: [`core/engine/providers/search-provider.interface.md`](../../../core/engine/providers/search-provider.interface.md)

## search — bağlı kaynaklar

| Öncelik | Kaynak | Tier | Kapsam notu |
|---|---|---|---|
| 1 | CourtListener (Free Law Project) | free | Federal içtihat, PACER dosyaları, yargıç profilleri, sözlü savunmalar |
| 2 | Trellis | paid | Eyalet ilk derece mahkemesi dosyaları, kararlar, hakim/karşı avukat analitiği |
| 3 | Westlaw (CoCounsel Legal, kuruluysa) | paid | Kapsamlı içtihat/mevzuat/ikincil kaynak — `external_plugins/cocounsel-legal` üzerinden |
| 4 | Federal Register API | free | Federal mevzuat/düzenleme metni ve yürürlük/yorum süresi tarihleri |

## preflightCheck — nasıl test edilir

CourtListener'a hafif bir "ping" sorgusu (ör. tek bir yaygın terim araması) gönderilir; 2 saniye içinde yapılandırılmış bir yanıt dönerse `available: true`. Dönmezse veya hata koduysa `available: false, reason: "<hata mesajı>"`.

## getSourceCatalog

Yukarıdaki tablo, [`mcp-tool-registry.us.yaml`](../mcp/mcp-tool-registry.us.yaml)'daki `capability_id: case-law-search` girdileriyle 1:1 eşleşir — her satırın `mcp_server.name` alanı burada listelenen kaynak adıyla aynıdır.
