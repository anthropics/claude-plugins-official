# Plugin Engine

Gerçek, çalıştırılabilir bir Python paketi — `claude-for-legal`'in ülke-bağımsız Plugin Engine'i. `core/`'un geri kalanı (interface/registry şemaları) **spesifikasyondur**; bu paket o spesifikasyonların **çalışan implementasyonudur**.

## Çalıştırma

```bash
# Repo kökünden:
python -m core.engine.plugin_engine .
```

Çıktı: keşfedilen her plugin'in adı, türü, versiyonu, lifecycle durumu; kayıtlı skill/guardrail fragment sayısı; her (Core Vertical × Country Plugin) çifti için kapasite kapsam raporu. Exit code, tüm plugin'ler `active` durumuna ulaştıysa `0`, herhangi biri hata verdiyse `1`.

## Bağımlılıklar

`jsonschema`, `pyyaml` — reponun zaten `scripts/validate.py` için kullandığı aynı iki paket. Yeni bir toolchain (Node/TypeScript, paket yöneticisi, build adımı) eklenmedi.

## Mimari — 13 özellik, 11 modül

| Özellik (istenen) | Modül | Ne yapar |
|---|---|---|
| **Plugin Discovery** | `discovery.py` | Dosya sistemini tarar (`repo_root`, `countries/*`, `external_plugins/*`); bir dizinin plugin olup olmadığını yalnızca `.claude-plugin/plugin.json` varlığına bakarak anlar. Hiçbir isim sabitlenmemiştir. |
| **Plugin Manifest** | `manifest.py` | `PluginManifest` — `plugin.json` + türe özgü dosyaları (`country.config.yaml`/`capabilities.yaml` ya da `extension-points.yaml`) tek bir yapıya toplar. `PluginKind` (COUNTRY/VERTICAL/VENDOR) **yapısal olarak** (hangi dosyalar var) belirlenir, isimden değil. |
| **Plugin Loader** | `loader.py` | `PluginEngine.load_all()` — Discovery → Manifest → Validation → Registration → Lifecycle'ı tek bir uçtan uca akışta yürütür; sonunda kapasite kapsam raporu üretir. |
| **Plugin Lifecycle** | `lifecycle.py` | `DISCOVERED → MANIFEST_LOADED → VALIDATED → REGISTERED → ACTIVE` (+ `FAILED`/`DISABLED`) durum makinesi; izin verilmeyen bir geçiş `LifecycleError` fırlatır. |
| **Plugin Registration** | `registry.py` → `PluginRegistry` | Yüklenen her plugin'i isimle kaydeder; isim çakışması `RegistrationError`. |
| **Country Registration** | `registry.py` → `CountryRegistry` | Ülke plugin'lerini `country_code` ile kaydeder. |
| **Prompt Registration** | `registry.py` → `PromptRegistry` | Her plugin'in `skills/*/SKILL.md` frontmatter'ını ve `core/shared/guardrail-fragments/*.md`'yi kataloglar. |
| **Tool Registration** | `registry.py` → `ToolRegistry` | Vertical'ların talep ettiği soyut `capability_id`'leri ve ülkelerin `mcp/*.yaml`'daki somut bağlamalarını kaydeder. |
| **Provider Registration** | `registry.py` → `ProviderRegistry` | `(provider_type, country_code) → tanım dosyası` eşlemesi. |
| **Plugin Configuration** | `config.py` | `active-country.yaml` işaretçi dosyasının okunması/yazılması (`load_active_country`/`set_active_country`) — gerçek yol parametre olarak verilir, test edilebilir. |
| **Plugin Validation** | `validation.py` | `country.config.yaml`/`capabilities.yaml`/`extension-points.yaml`'ı ilgili JSON Schema'ya (`core/engine/registries/*.schema.yaml`) karşı doğrular + `[PLACEHOLDER]` tespiti. |
| **Plugin Versioning** | `versioning.py` | `SemVer` (`plugin.json`'ın `MAJOR.MINOR.PATCH`'i) ve `InterfaceVersion` (`@YYYY-MM`) ayrıştırma/karşılaştırma; `loader.py` bunu gerçekten kullanır — bir ülkenin `capabilities.yaml`'daki `provider_versions`'ı ilgili interface dosyasının frontmatter'ındaki versiyondan eskiyse uyarı üretir. |
| **Plugin Dependency** | `dependency.py` | (a) `resolve_capability_coverage` — bir vertical'ın ihtiyaçları ile bir ülkenin sağladıkları arasındaki kapsam farkı; (b) `resolve_load_order` — genel, `depends_on` tabanlı topolojik sıralama (bugün hiçbir plugin kullanmıyor, altyapı hazır). |

Ek: `errors.py` (istisna hiyerarşisi), `frontmatter.py` (SKILL.md/interface `.md` dosyalarındaki YAML frontmatter'ı ayrıştıran paylaşılan yardımcı).

## "Core plugin'lerden bağımsız olmalı" — nasıl doğrulandı

```bash
grep -rEn "employment-legal|commercial-legal|countries/tr|countries/us" core/engine/plugin_engine/*.py
# -> 0 eşleşme
```

Motor kodu hiçbir plugin adı, ülke kodu ya da yol içermez — her şey `discovery.py`'nin çalışma zamanında bulduğu dizinlerden gelir. Bu depoya yeni bir plugin (örn. `countries/de`) eklendiğinde, motorun tek satırı değişmeden onu keşfeder ve yükler — "her plugin runtime sırasında yüklenebilmeli" gereksiniminin somut kanıtı.

## Bilinçli sınırlar

- Bu motor **Claude Code/Cowork runtime'ının kendisi değildir** — Claude bir konuşma sırasında bu Python kodunu çalıştırmaz. Bu, repo bakımı, CI doğrulaması ve gelecekteki bir "compose/deploy" adımı için kullanılan **bağımsız bir araçtır** (`scripts/lint-country-plugin.py`'nin kavramsal halefi, jsonschema + yapısal kontrollerin ötesine geçen tam bir yaşam döngüsü/registry modeliyle).
- Test altyapısı (pytest vb.) reponun geri kalanında da yok; bu paket gerçek repo'ya karşı çalıştırılarak ve yukarıdaki gibi kenar-durum betikleriyle doğrulanmıştır (bkz. commit mesajı).
