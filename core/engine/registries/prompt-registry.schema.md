---
component: prompt-registry
version: "@2026-07"
status: stable
scope: core (ülke bağımsız)
---

# Prompt Registry

## Sorumluluk

Tüm Skill/Prompt şablonlarının (`SKILL.md`, `CLAUDE.md`) ve **paylaşılan guardrail fragment'larının** merkezi kataloğu. İki şeyi çözer:

1. **Kod tekrarının önlenmesi:** Bugün her plugin'in `CLAUDE.md`'sinde birebir kopyalanmış olan ortak bloklar (Destination check, No silent supplement, Jurisdiction recognition, Reviewer note formatı, Cross-skill severity floor...) tek kaynaklı hale getirilir — bkz. [`core/shared/guardrail-fragments/`](../../shared/guardrail-fragments/).
2. **Ülkeye-özgü yer tutucu çözümleme:** Bir Core Vertical skill'i `{{country.X}}` biçiminde bir yer tutucu içerdiğinde, bu değerin çalışma zamanında nasıl doldurulacağını tanımlar.

## Kayıt Birimleri

| Birim | Kimlik | Kaynak |
|---|---|---|
| Skill şablonu | `(vertical, skill_id, version)` | `<vertical>/skills/<skill_id>/SKILL.md` |
| Guardrail fragment | `fragment_id` | `core/shared/guardrail-fragments/<fragment_id>.md` |
| Country guardrail overlay | `(fragment_id, country_code)` | `countries/<code>/knowledge/<vertical>/overlays/<fragment_id>.md` (opsiyonel, yoksa Core fragment aynen kullanılır) |

## Yer Tutucu Sözlüğü (ilk küme — genişletilebilir)

| Yer tutucu | Kaynağı | Örnek çözümlenmiş değer (TR) |
|---|---|---|
| `{{country.privilegeHeader}}` | Country Config → `privilege_doctrine` | `"GİZLİ — İÇ HUKUKİ DEĞERLENDİRME"` |
| `{{country.barReferralText}}` | Country Config → `professional_regulator` | `"Türkiye Barolar Birliği"` |
| `{{country.citationTagVocabulary}}` | Citation Provider → `getProvenanceTagVocabulary()` | `[Yargıtay]`, `[Resmi Gazete]` |
| `{{country.name}}` | Country Config → `country_name` | `"Türkiye"` |

Bir yer tutucu çözümlenemezse (ör. Country Config eksik alan bırakmışsa), Prompt Registry bunu **boş bırakmaz** — `[COUNTRY CONFIG EKSİK: <alan adı>]` şeklinde açıkça işaretler, skill bu işaretle karşılaştığında kullanıcıyı bilgilendirip durur (bkz. reponun mevcut "PLACEHOLDER" tespiti ile cold-start-interview'e yönlendirme deseni — burada genellenmiştir).

## Versiyonlama

Her skill şablonu `skill_id@version` biçiminde sürümlenir (ör. `wage-hour-qa@2.1`). Bir Country Plugin, `capabilities.yaml` içinde hangi skill şablon versiyonuna karşı içerik ürettiğini beyan eder — böylece Core bir skill'i önemli ölçüde değiştirdiğinde (ör. yeni zorunlu bir adım eklediğinde), hangi ülke paketlerinin güncellenmesi gerektiği izlenebilir.

## Guardrail Fragment Çözümleme Sırası

1. Core fragment yüklenir (`core/shared/guardrail-fragments/<fragment_id>.md`).
2. Aktif ülkenin bir overlay'i varsa (`countries/<code>/knowledge/<vertical>/overlays/<fragment_id>.md`), bu overlay Core fragment'ın **üzerine eklenir** (üzerine yazmaz) — ör. "jurisdiction-recognition" fragment'ının temel metni sabit kalır, ülkeye özgü bir ek not (varsa) altına eklenir.
3. Hiçbir overlay Core fragment'ın güvenlik/guardrail özünü (ör. "no silent supplement" kuralının kendisini) geçersiz kılamaz — overlay'ler yalnızca **ek bağlam** sağlayabilir, bir guardrail'i zayıflatamaz.

## Değişiklik Günlüğü

- `@2026-07` — İlk yayın (bu commit).
