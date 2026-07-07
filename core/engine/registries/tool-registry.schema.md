---
component: tool-registry
version: "@2026-07"
status: stable
scope: core (ülke bağımsız)
---

# Tool Registry

## Sorumluluk

Skill'lerin ihtiyaç duyabileceği **soyut yetenekleri (capability)** kataloglar ve bu yeteneklerin somut bir Country Plugin'e bağlanırken uyması gereken **en-az-yetki (least-privilege) politikasını** zorunlu kılar. Tool Registry, hiçbir somut MCP sunucusu adı bilmez — "hangi soyut yeteneğin hangi somut sunucuya bağlandığı" [`mcp-tool-registry.schema.yaml`](./mcp-tool-registry.schema.yaml)'nin işidir.

## Soyut Yetenek Kataloğu

| `capability_id` | Açıklama | Tipik kullanan vertical |
|---|---|---|
| `case-law-search` | İçtihat/mevzuat arama | litigation-legal, employment-legal, ip-legal |
| `e-signature` | İmza/zarf durumu sorgulama | commercial-legal, corporate-legal |
| `e-discovery-read` | Delil/üretim seti okuma | litigation-legal |
| `entity-registry-lookup` | Tüzel kişilik sicil sorgusu | corporate-legal |
| `regulatory-feed` | Resmî mevzuat/düzenleyici duyuru akışı | regulatory-legal, ai-governance-legal |
| `calendar-deadline` | İş günü/tatil hesaplı süre takibi | corporate-legal, litigation-legal, employment-legal |
| `document-management` | DMS/CLM meta verisi okuma | commercial-legal, corporate-legal |
| `native:read` / `native:write` / `native:grep` / `native:glob` / `native:web-fetch` / `native:web-search` | Claude Code/Cowork'ün yerleşik araçları | tümü |

Bu liste kapalı değildir; yeni bir vertical yeni bir `capability_id` tanımlayabilir, ancak tanım burada (Core'da) yapılır — bir Country Plugin kendi capability_id'sini icat edemez (aksi halde iki ülke aynı yeteneği farklı isimlerle tanımlar ve karşılaştırılamaz hale gelir).

## Çözümleme Sözleşmesi

```
resolve(capability_id, active_country) → binding | NOT_AVAILABLE
```

Bu fonksiyon [Plugin Loader](../plugin-loader/PLUGIN_LOADER_PROTOCOL.md) tarafından çağrılır; Tool Registry'nin kendisi bir yürütme motoru değildir, yalnızca **hangi capability_id'lerin geçerli olduğunu ve hangi tier kısıtlarına tabi olduğunu** tanımlar.

## En-Az-Yetki (Least-Privilege) Politikası — zorunlu, ülkeden bağımsız

Bu politika `managed-agent-cookbooks`'un bugün zaten uyguladığı üç-katmanlı modelin Core seviyesinde resmîleştirilmiş halidir; hiçbir Country Plugin bunu gevşetemez:

1. **Reader tier** — yalnızca `native:read`, `native:grep`, `native:glob`. Güvenilmeyen belge/kaynak içeriğini yapılandırılmış veriye indirger. `native:write` ve hiçbir `mcp_toolset` **asla** bu katmanda açık olamaz.
2. **Analyzer tier** — Reader'ın çıktısını + salt-okunur MCP erişimini (`case-law-search`, `regulatory-feed` gibi) alır. `native:write` yok.
3. **Writer tier** — Nihai çıktıyı üreten tek katman; yalnızca bu katmanda `native:write` açık olabilir. Ham/güvenilmeyen belgeyi asla doğrudan görmez.

`scripts/lint-tool-scope.py` (mevcut) bu kuralı bugün `managed-agent-cookbooks/*/agent.yaml` üzerinde zorunlu kılıyor; bu doküman aynı kuralı **Core politikası** olarak isimlendirir ki ileride Core Vertical'ların kendi tool bağlamaları da aynı denetime tabi olsun.

## Kademeli Bozulma (Graceful Degradation)

`resolve()` bir `capability_id` için hiçbir binding bulamazsa `NOT_AVAILABLE` döner. Çağıran skill bunu **asla** sessizce atlayamaz — kullanıcıya "bu ülkede bu yetenek şu an bağlı değil" şeklinde açıkça bildirmek zorundadır (bkz. [`../providers/CONVENTIONS.md`](../providers/CONVENTIONS.md) §3, aynı üç-değerli semantik burada da geçerlidir).

## Değişiklik Günlüğü

- `@2026-07` — İlk yayın (bu commit).
