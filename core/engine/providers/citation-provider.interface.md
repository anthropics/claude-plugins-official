---
interface: citation-provider
version: "@2026-07"
status: stable
implemented-by: countries/<code>/providers/citation-provider.<code>.md
conventions: ./CONVENTIONS.md
---

# Citation Provider

## Sorumluluk

Bir hukuki referansı (kanun maddesi, içtihat, düzenleme) **ülkenin standart atıf biçiminde** metne çevirir ve o atfın taşıdığı **uydurma (fabrication) riskini** sınıflandırır. Bu arayüz, atfın *doğru olup olmadığını* doğrulamaz — yalnızca *nasıl yazılacağını* ve *hangi doğrulamanın öncelikli olduğunu* bilir.

Ortak kurallar için bkz. [`CONVENTIONS.md`](./CONVENTIONS.md) — versiyonlama, hata semantiği ve etiket sözlüğü taban kuralları burada tekrar edilmez.

## Bağımlılık yönü

Bir Core Vertical skill'i (ör. `employment-legal/skills/wage-hour-qa/SKILL.md`) bu arayüze bağımlıdır, herhangi bir ülkenin atıf biçimine değil. Somut biçim, çalışma zamanında aktif Country Plugin'in implementasyonundan enjekte edilir. Skill metninin içinde `"29 U.S.C. §207(e)"` gibi belirli bir ülkenin atıf kalıbı **sabit metin olarak asla geçmez**; bunun yerine "aktif ülkenin Citation Provider'ı ile biçimlendir" adımı geçer.

## Metod Sözleşmeleri

| Metod | Girdi | Çıktı | Açıklama |
|---|---|---|---|
| `formatStatuteCitation(reference)` | `{ instrument: string, section: string, subsection?: string }` | `string` | Bir kanun/mevzuat maddesini ülkenin standart atıf biçimine çevirir. |
| `formatCaseCitation(reference)` | `{ court?: string, caseNumber?: string, date?: string, reporter?: string, freeText?: string }` | `string` | Bir içtihadı ülkenin standart atıf biçimine çevirir. Yapılandırılmış alanlar yoksa `freeText` üzerinden en iyi çaba (best-effort) biçimlendirme yapılır ve sonuç `[best-effort format]` ile işaretlenir. |
| `getProvenanceTagVocabulary()` | — | `TagDefinition[]` — `{ tag: string, sourceDescription: string, requiresLiveToolResult: boolean }` | Bu ülke için geçerli olan, Core'un taban sözlüğüne (bkz. CONVENTIONS §4) eklenen ülkeye-özgü etiketlerin listesi. |
| `getHighRiskPinpointPatterns()` | — | `PatternDescriptor[]` — `{ patternName: string, description: string, example: string }` | Bu ülkenin atıf biçiminde "en yüksek uydurma riski" taşıyan pinpoint kalıpları (madde/fıkra/paragraf numarası şekli gibi) — reponun mevcut "pinpoint cites carry the highest fabrication risk" ilkesinin ülkeye-özgü somutlaşması. |
| `classifyCitationRisk(citationText)` | `string` | `{ tier: "high" \| "medium" \| "low", reason: string }` | Verilen bir atıf metnini, `getHighRiskPinpointPatterns()` çıktısına göre sınıflandırır. |

## Dönüş Semantiği

Bkz. CONVENTIONS §3. Özellikle: bir ülke belirli bir atıf türünü (ör. bölge/eyalet-bazlı içtihat) desteklemiyorsa `formatCaseCitation` `NOT_AVAILABLE` döner — asla boş string ya da genel bir varsayılan biçim üretmez.

## Kapsam Dışı (Non-goals)

- **Atfın doğruluğunu doğrulamaz.** Bir atfın gerçekten var olup olmadığı, güncel olup olmadığı Search Provider'ın ve nihayetinde inceleyen avukatın sorumluluğundadır (bkz. reponun mevcut "quote-to-proposition check" guardrail'i — değişmedi).
- **Arama yapmaz.** Kaynak bulma [`search-provider.interface.md`](./search-provider.interface.md)'nin sorumluluğundadır.
- **Atıf geçmişi tutmaz.** Doğrulama kayıtları (verification-log) practice profile seviyesinde kalmaya devam eder; bu arayüzün kapsamı dışındadır.

## Uyumluluk Kontrol Listesi (Country Plugin için)

Bir Country Plugin bu arayüzü implemente ettiğini beyan etmeden önce:

- [ ] Her 5 metod için `full` / `partial` / `not_supported` durumu `capabilities.yaml`'da beyan edilmiş.
- [ ] `getProvenanceTagVocabulary()` çıktısındaki her etiket, gerçek bir bağlı kaynağa (Legal Source Registry girdisi) karşılık geliyor — icat edilmiş etiket yok.
- [ ] `getHighRiskPinpointPatterns()` en az bir somut örnek (`example`) içeriyor.

## Değişiklik Günlüğü

- `@2026-07` — İlk yayın (bu commit).
