# `core/` — Ülke Bağımsız Çekirdek

Bu dizin, `claude-for-legal` marketplace'inin **ülke bağımsız çekirdeğini** barındırır. Hiçbir dosyanın bir ülke adı, kanun numarası, mahkeme adı, düzenleyici kurum adı ya da connector URL'i içermemesi bu dizin için bir tasarım kuralıdır — bir dosyada bunlardan biri görülüyorsa bu bir tasarım hatasıdır ve `countries/<code>/` altına taşınmalıdır.

## Neden var

Bugüne kadar her plugin (`employment-legal`, `commercial-legal`, `litigation-legal`, ...) kendi guardrail metnini birebir kopyalıyor ve ülkeye özgü varsayımları (CourtListener, DocuSign, USPTO, FLSA, ABD eyalet sistemi...) doğrudan skill metnine gömüyordu. Bu, yeni bir pazara (Türkiye, Almanya, Fransa, İngiltere, BAE, Suudi Arabistan) açılmayı her seferinde ilgili skill'in yeniden yazılmasını gerektiren bir işe çeviriyordu.

`core/`, bu bağımlılığı tersine çevirir:

- **Dependency Injection (Bağımlılık Enjeksiyonu):** Core Vertical'lar (mevcut plugin'ler: `employment-legal`, `commercial-legal`, vb.) artık somut bir ülkenin hukuk sistemine değil, bu dizindeki **soyut sözleşmelere (interface)** bağımlıdır. Hangi somut implementasyonun kullanılacağı, derleme zamanında değil, **çalışma zamanında** — hangi Country Plugin'in kurulu ve aktif olduğuna göre — belirlenir ("enjekte edilir"). Core, hiçbir zaman `countries/tr/` ya da `countries/us/` içeriğini doğrudan import etmez/bilmez.
- **Provider Pattern:** Her dış bağımlılık kategorisi (atıf biçimlendirme, hukuki arama, belge/imza durumu) bir *Provider* olarak soyutlanmıştır. Bir Provider, "ne yapılır"ı tanımlar ("nasıl yapılır"ı değil); somut implementasyon her zaman bir Country Plugin'e aittir.
- **Plugin Pattern:** Country Plugin'ler, Core'un onların varlığından haberdar olmasına gerek kalmadan bu sözleşmelere "takılır" (açık/kapalı ilke — Core, yeni bir ülke eklendiğinde değişmez).

## Bu dizin ne içerir

```
core/
└── engine/
    └── providers/
        ├── CONVENTIONS.md                    # 3 arayüzün paylaştığı ortak kurallar (versiyonlama, hata semantiği, etiket sözlüğü)
        ├── citation-provider.interface.md     # Atıf biçimlendirme sözleşmesi
        ├── search-provider.interface.md       # Hukuki araştırma sözleşmesi
        ├── document-provider.interface.md     # Belge/imza/dosyalama durumu sözleşmesi
        └── country-config.schema.yaml         # Her ülkenin kök meta-veri şeması
```

## Bu dizin ne içermez (henüz)

- **Registry şemaları** (`tool-registry`, `prompt-registry`, `mcp-tool-registry`, `legal-source-registry`) — ayrı bir commit'te eklenecek.
- **Plugin Loader protokolü** (aktivasyon/keşif mekanizması) — ayrı bir commit'te eklenecek.
- **Guardrail Fragment kütüphanesi** — ayrı bir commit'te eklenecek.
- **Somut implementasyonlar** — bunlar hiçbir zaman `core/` altında olmayacak; her zaman `countries/<code>/providers/` altında yaşayacak.

## Bu commit'in etki alanı

Bu commit **tamamen ekleyicidir**. Hiçbir mevcut dosya değişmedi, hiçbir skill henüz bu sözleşmelere referans vermiyor. Mevcut 12 plugin, önceki davranışıyla birebir çalışmaya devam ediyor.
