# United States — Citation Provider

Bkz. sözleşme: [`core/engine/providers/citation-provider.interface.md`](../../../core/engine/providers/citation-provider.interface.md)

## formatStatuteCitation

**Kalıp:** `Title U.S.C. §Section(Subsection)` (federal); eyalet kanunları için `[Eyalet kısaltması] [Kod Adı] §Section`

**Örnekler:**
- `29 U.S.C. §207(e)` — FLSA aşırı mesai/"regular rate" tanımı
- `29 U.S.C. §216(b)` — likidite edilmiş tazminat
- `29 U.S.C. §255(a)` — zamanaşımı
- `Cal. Lab. Code §2775` — Kaliforniya ABC testi kodifikasyonu

## formatCaseCitation

**Kalıp:** `Case Name, Volume Reporter Page (Court Year)`
**Örnek:** `Dynamex Operations W. v. Superior Court, 4 Cal. 5th 903 (2018)`

## getProvenanceTagVocabulary

| Etiket | Kaynak açıklaması | Canlı araç sonucu gerektirir mi? |
|---|---|---|
| `[CourtListener]` | Free Law Project'in federal içtihat/PACER veri platformu | evet |
| `[Trellis]` | Eyalet ilk derece mahkemesi veri seti | evet |
| `[Westlaw]` | Thomson Reuters CoCounsel Legal (kuruluysa) | evet |
| `[Federal Register]` | Federal Register API | evet |

## getHighRiskPinpointPatterns

| Kalıp adı | Açıklama | Örnek |
|---|---|---|
| `subsection-letter` | Alt-fıkra harfi (ör. §207(e) içindeki (1)-(7) alt bentleri) uydurma riski yüksek | `29 U.S.C. §207(e)(2)` |
| `state-carve-out` | Eyalete özgü istisna alt maddeleri (ör. CA Lab. Code §§2775/2776/2783) | `Cal. Lab. Code §2783(k)` |
| `element-count` | Bir testin (ör. ABC testi) kaç unsurdan oluştuğu — model bazen unsur sayısını yanlış hatırlar | "ABC testi 3 unsurdan oluşur" |

## classifyCitationRisk — kural özeti

Yukarıdaki üç kalıptan biriyle eşleşen herhangi bir pinpoint atıf `high` risk taşır ve `[verify]` etiketiyle işaretlenir; genel madde/bölüm düzeyi atıflar (alt-fıkra olmadan) `medium`; kurum adı/genel çerçeve referansları `low`.
