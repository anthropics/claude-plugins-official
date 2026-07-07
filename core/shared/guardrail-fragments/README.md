# `core/shared/guardrail-fragments/` — Kanonik Guardrail Kütüphanesi

Bu dizin, bugün her plugin'in `CLAUDE.md`'sinde **birebir kopyalanmış** olarak duran ortak guardrail metinlerinin **tekilleştirilmiş, tek-kaynaklı** hâlidir.

## Neden var

`CONTRIBUTING.md`'nin kendi ilkesi: *"SKILL.md encodes the right behavior; CLAUDE.md guardrails are the net."* Ama bu net bugüne kadar 12 kopyada duruyordu — biri değiştiğinde diğer 11'i sessizce eskiyor (drift). Bu dizin bunu tek kopyaya indirir.

## Kullanım kuralı

- Bir plugin'in `CLAUDE.md`'si artık bu fragment'ların metnini **kopyalamaz**, onlara **referans verir** (ör. `Bkz. core/shared/guardrail-fragments/destination-check.md`).
- Bir Country Plugin, bir fragment'ın **üzerine ek** (overlay) sağlayabilir (`countries/<code>/knowledge/<vertical>/overlays/<fragment_id>.md`) — ama fragment'ın güvenlik özünü asla zayıflatamaz. Bkz. [`prompt-registry.schema.md`](../../engine/registries/prompt-registry.schema.md) → "Guardrail Fragment Çözümleme Sırası".
- Bu dizindeki bir fragment değiştiğinde, ona referans veren **her** plugin otomatik olarak güncel kalır — ayrı ayrı düzenlenmesi gerekmez.

## İçerik

| Fragment | Kapsadığı |
|---|---|
| [`destination-check.md`](./destination-check.md) | Çıktının nereye gittiğinin, ayrıcalık/gizlilik çemberine göre kontrolü |
| [`no-silent-supplement.md`](./no-silent-supplement.md) | Bilgi boşluklarında üç geçerli tepki; kullanıcı-beyanlı gerçeklerin doğrulanması |
| [`jurisdiction-recognition.md`](./jurisdiction-recognition.md) | Yargı yetkisi tespiti, legal family farklılıkları, kavramsal karşılıksızlık |
| [`reviewer-note-format.md`](./reviewer-note-format.md) | Standart "⚠️ Reviewer note" bloğu ve karar ağacı formatı |
| [`cross-skill-severity-floor.md`](./cross-skill-severity-floor.md) | Şiddet derecesi tabanı; öznel hukuki kararlarda geri-alınabilir-hata tercihi |
| [`retrieved-content-trust.md`](./retrieved-content-trust.md) | Alınan içeriğin veri olduğu, komut olmadığı kuralı; araç-vs-model çelişkisi |
| [`large-input-output.md`](./large-input-output.md) | Büyük girdi/çıktıda kapsam yönetimi, sessiz kesinti önleme |
| [`scaffolding-not-blinders.md`](./scaffolding-not-blinders.md) | Kontrol listesinin taban olması, doğru skill'e yönlendirme, orantılılık |
| [`source-attribution.md`](./source-attribution.md) | Etiket sözlüğü, provenance kuralları, alıntılanan bir kanunla anlaşmazlık |
| [`proportionality.md`](./proportionality.md) | Soru türüne göre yanıt boyutlandırma, aşırı-hukukileştirmeden kaçınma |

*Not: `source-attribution.md` ve `proportionality.md`, Commit 4'ten sonra, Commit 15'te `employment-legal`'e gerçekten uygulanırken keşfedilen ek tekrarlardır — kütüphane sabit değil, uygulama sırasında büyüyebilir.*

## Bu commit'in etki alanı

Bu commit tamamen ekleyicidir. Hiçbir plugin `CLAUDE.md`'si henüz bu fragment'lara referans vermiyor — mevcut kopyalanmış metinler yerinde duruyor (silme, ayrı ve izole bir sonraki dalgada yapılacak, bkz. migration planı §1.4).
