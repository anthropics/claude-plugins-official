# `countries/` — Ülke Plugin'leri

Her alt dizin, bağımsız olarak kurulabilir bir Claude Code/Cowork plugin'idir ve bir veya daha fazla Core Vertical'a (mevcut `employment-legal/`, `commercial-legal/`, ... dizinleri) ülkeye özgü içerik sağlar:

- **Country Config** (`country.config.yaml`) — [`core/engine/providers/country-config.schema.yaml`](../core/engine/providers/country-config.schema.yaml) şemasına uygun kök meta-veri.
- **Capabilities** (`capabilities.yaml`) — bu ülkenin hangi Provider metodlarını `full`/`partial`/`not_supported` olarak sağladığının beyanı.
- **Provider implementasyonları** (`providers/`) — [Citation](../core/engine/providers/citation-provider.interface.md), [Search](../core/engine/providers/search-provider.interface.md), [Document](../core/engine/providers/document-provider.interface.md) arayüzlerinin somut bağlamaları.
- **MCP Tool Registry** (`mcp/`) — [`mcp-tool-registry.schema.yaml`](../core/engine/registries/mcp-tool-registry.schema.yaml)'ye uygun somut connector bağlamaları.
- **Legal Source Registry** (`legal-sources/`) — [`legal-source-registry.schema.yaml`](../core/engine/registries/legal-source-registry.schema.yaml)'ye uygun otorite kataloğu.
- **Knowledge Packs** (`knowledge/<vertical>/`) — her vertical için ülkeye özgü içerik (testler, formüller, takvimler).
- **Profiles** (`profiles/`) — `company-profile-template.md`'nin yerelleştirilmiş hâli.

## Yeni bir ülke eklemek

1. [`_template/`](./_template/) dizinini `countries/<iso-alpha-2-kod>/` olarak kopyala.
2. Her `.TEMPLATE.` uzantılı dosyayı doldur ve uzantıyı kaldır (ör. `citation-provider.TEMPLATE.md` → `citation-provider.tr.md`).
3. `scripts/lint-country-plugin.py`'yi çalıştır (henüz eklenmedi — bkz. bir sonraki dalga).
4. `.claude-plugin/plugin.json` ekleyerek kurulabilir hale getir, `.claude-plugin/marketplace.json`'a kaydet.

## Mevcut ülke plugin'leri

*(Bu commit itibarıyla henüz yok — `countries/us` ve `countries/tr` sonraki dalgalarda eklenecek.)*
