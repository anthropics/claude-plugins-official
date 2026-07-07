---
component: plugin-loader
version: "@2026-07"
status: stable
scope: core (ülke bağımsız)
---

# Plugin Loader Protokolü

## Sorumluluk

Hangi Core Vertical'ların kurulu olduğunu ve hangi Country Plugin'in **aktif** olduğunu tespit eder; bir skill her çalıştığında Country Config'i yükler, [Tool Registry](../registries/tool-registry.schema.md) üzerinden gerekli capability bağlamalarını çözümler, eksik/uyumsuz olanı [Coverage Report](./COVERAGE_REPORT_FORMAT.md) olarak raporlar.

Bu bir yürütme motoru (çalışan bir program) değildir — bir **protokol**dür: her Core Vertical skill'inin adım listesinin başında izlemesi gereken, düz metin olarak ifade edilmiş bir sıra.

## Aktivasyon El Sıkışması (Activation Handshake)

1. Kullanıcı bir Country Plugin kurar (ör. `countries/tr`).
2. Country Plugin'in kendi aktivasyon skill'i (bir sonraki dalgada eklenecek `activate` skill'i) çalıştırıldığında, aktif ülkeyi paylaşılan bir işaretçi dosyasına yazar: `~/.claude/plugins/config/claude-for-legal/active-country.yaml` (bkz. [`active-country.template.yaml`](./active-country.template.yaml)).
3. Bu dosya, **tüm Core Vertical'ların ortak okuma noktasıdır** — reponun bugün zaten kullandığı practice-profile konvansiyonunun (`~/.claude/plugins/config/claude-for-legal/<plugin>/CLAUDE.md`) doğal bir uzantısıdır, yeni bir mekanizma icat etmez.
4. Birden fazla Country Plugin aynı anda kuruluysa ve işaretçi belirsizse, Plugin Loader **varsayım yapmaz** — skill kullanıcıya "birden fazla ülke plugin'i kurulu, hangisini aktif etmek istersiniz?" diye sormak zorundadır.

## Çözümleme Sırası (bir skill her çalıştığında)

```
1. active-country.yaml oku → aktif country_code (yoksa: "aktif ülke yok" durumuna düş, bkz. Geriye Uyumluluk)
2. countries/<code>/country.config.yaml yükle
3. countries/<code>/capabilities.yaml yükle
4. Çalışan vertical'ın extension-points.yaml'ını yükle
5. İkisini karşılaştır → Coverage durumu (full / partial / not_applicable / missing)
6. Eksik/kısmi olan her şeyi Coverage Report'a yaz
7. Skill'i, çözümlenmiş Country Config + Provider bağlamalarıyla başlat
```

## Kapasite Müzakeresi (Capability Negotiation)

`extension-points.yaml` (vertical'ın talep ettiği) ile `capabilities.yaml` (ülkenin sağladığı) karşılaştırılırken üç sonuç mümkündür:

| Sonuç | Anlamı | Skill'in davranışı |
|---|---|---|
| `full` | Vertical'ın istediği her şey `full` olarak beyan edilmiş | Normal çalışır |
| `partial` | Bazı metodlar `partial`/`not_supported` | Skill çalışır ama eksik kısmı **açıkça** kullanıcıya bildirir |
| `missing` | Ülke plugin'i bu vertical için hiç `capabilities.yaml` girdisi içermiyor | Skill, bu vertical'ın bu ülkede desteklenmediğini söyler ve durur — **asla varsayılan/ABD davranışına sessizce düşmez** (geçiş dönemi istisnası hariç, bkz. aşağı) |

## Geriye Uyumluluk — Aktif Ülke Yokken

Hiçbir Country Plugin kurulu/aktif değilse (bugünkü kullanıcılar dahil), Plugin Loader `NOT_AVAILABLE` sinyali üretir ve her parametrize edilmiş skill, kendi içinde tuttuğu **gömülü varsayılan davranış bloğuna** (geçiş dönemi boyunca `countries/us` içeriğiyle senkron tutulan) düşer. Bu, mevcut kullanıcıların hiçbir ülke plugin'i kurmadan bugünküyle birebir aynı deneyimi almaya devam etmesini garanti eder. Bu istisna yalnızca "aktif ülke yok" durumu için geçerlidir — "aktif ülke var ama capability eksik" durumunda geçerli değildir (o durumda yukarıdaki `missing` satırı uygulanır).

## Sorumlu Olmadığı Şeyler

- Somut Provider implementasyonlarını **yazmaz/barındırmaz** — yalnızca hangisinin aktif olduğunu bulur.
- Kullanıcı arayüzü sunmaz — bir Claude Code/Cowork skill'inin izleyeceği talimat kümesidir.
- MCP sunucularıyla doğrudan konuşmaz — bu [MCP Tool Registry](../registries/mcp-tool-registry.schema.yaml) bağlamalarının işidir.

## Değişiklik Günlüğü

- `@2026-07` — İlk yayın (bu commit).
