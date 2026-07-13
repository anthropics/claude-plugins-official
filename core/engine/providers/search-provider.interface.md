---
interface: search-provider
version: "@2026-07"
status: stable
implemented-by: countries/<code>/providers/search-provider.<code>.md
conventions: ./CONVENTIONS.md
---

# Search Provider

## Sorumluluk

"Bir hukuki araştırma sorgusu gönder, kaynaklı ve provenance'ı (kaynağın izini) belli sonuç al" sözleşmesini soyutlar. Bugünkü CourtListener/Westlaw/Trellis/Federal Register gibi somut connector'ların yerini alan **tek bir davranış sözleşmesidir** — Core Vertical skill'leri hiçbir zaman somut bir connector adı bilmez.

Ortak kurallar için bkz. [`CONVENTIONS.md`](./CONVENTIONS.md).

## Bağımlılık yönü

Bir Core Vertical skill'i şu şekilde yazılır: *"Aktif ülkenin Search Provider'ı ile içtihat/mevzuat ara."* Hangi somut MCP sunucusunun (UYAP, Yargıtay karar arama, CourtListener, Westlaw...) bu isteği karşılayacağı, çalışma zamanında MCP Tool Registry üzerinden çözümlenir (ayrı commit). Bu arayüz dosyası hiçbir somut sunucu adı içermez.

## Metod Sözleşmeleri

| Metod | Girdi | Çıktı | Açıklama |
|---|---|---|---|
| `search(request)` | `{ query: string, jurisdictionScope?: string, sourceType?: "case-law" \| "statute" \| "regulation" \| "administrative", dateRange?: { from?: string, to?: string } }` | `SearchResult[]` | Kaynaklı hukuki bilgi arar. |
| `preflightCheck()` | — | `{ available: boolean, sourceId?: string, reason?: string }` | Bağlı bir araştırma connector'ının o oturumda **gerçekten yanıt verip vermediğini** test eder — reponun mevcut "pre-flight citation check" guardrail'inin resmi sözleşmesi. Skill, herhangi bir atıf yapmadan önce bunu çağırmak zorundadır. |
| `getSourceCatalog()` | — | `SourceDescriptor[]` — `{ sourceId: string, tier: "free" \| "paid", coverage: string }` | Bu ülke için bağlı somut kaynakların listesi — ücretsiz/ücretli katman ayrımı dahil (bugünkü "Federal Register API ücretsiz / Westlaw ücretli" iki-katmanlı desenin genel karşılığı). |

`SearchResult` şekli: `{ title: string, citationRaw: string, url?: string, retrievedAt: string, sourceId: string, snippet?: string }`

## Dönüş Semantiği

Bkz. CONVENTIONS §3. `search()` sıfır sonuç döndürdüğünde bu `NOT_AVAILABLE` ile **karıştırılmaz** — sıfır sonuç, sorgunun çalıştığını ama eşleşme bulunamadığını gösteren geçerli bir `RESULT`'tır (boş dizi). `NOT_AVAILABLE`, connector'ın hiç yanıt vermediği veya bu ülke için hiç bağlanmadığı durum için ayrılmıştır. Bu ayrımın karıştırılması, reponun mevcut "no silent supplement" ilkesini ihlal eder (bir skill, "sonuç yok" ile "arama hiç çalışmadı"yı birbirine karıştırıp sessizce model bilgisine geçemez).

## Kapsam Dışı (Non-goals)

- **Atıf biçimlendirmez.** Ham sonuçları ülkenin standart atıf biçimine çevirmek [`citation-provider.interface.md`](./citation-provider.interface.md)'nin işidir.
- **Yazma/gönderme yapmaz.** Salt okunurdur (bkz. CONVENTIONS §5).
- **Sonucun hukuki geçerliliğini değerlendirmez.** "Bu bir holding mi, dictum mu, reddedilmiş bir argüman mı" değerlendirmesi (reponun mevcut "quote-to-proposition check" guardrail'i) skill/inceleyen avukat seviyesinde kalır.

## Uyumluluk Kontrol Listesi (Country Plugin için)

- [ ] `preflightCheck()` gerçek bir bağlı connector'a karşı test edilmiş; sahte/her zaman `true` dönen bir stub değil.
- [ ] `getSourceCatalog()`'daki her `sourceId`, MCP Tool Registry'de karşılığı olan somut bir girdiye işaret ediyor.
- [ ] En az bir `tier: "free"` kaynak beyan edilmiş **veya** hiç ücretsiz kaynak yoksa bu açıkça `capabilities.yaml`'da not düşülmüş (sessizce atlanmamış).

## Değişiklik Günlüğü

- `@2026-07` — İlk yayın (bu commit).
