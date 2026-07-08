# `plugins/turkey/` — Executable Turkey Country Plugin

Bu, `countries/tr/`'nin (markdown/YAML **spesifikasyonu**) gerçek, çalıştırılabilir Python koduyla **implementasyonudur**. İkisi farklı roller oynar:

| | Rol | Örnek |
|---|---|---|
| `countries/tr/` | **Veri/spec** — hukuki içerik, tek doğruluk kaynağı | `country.config.yaml`, `knowledge/employment-legal/overtime-framework.md` |
| `core/engine/plugin_engine/contracts.py` | **Soyut sözleşme** — ülkeden bağımsız arayüzler | `CitationProvider`, `SearchProvider` Protocol'leri |
| `plugins/turkey/` (bu dizin) | **Davranış** — sözleşmeleri `countries/tr/` verisiyle dolduran çalışan kod | `TurkishCitationProvider`, `OvertimeQaWorkflow` |

Bu ayrım Dependency Inversion Principle'ın doğrudan uygulamasıdır: `plugins/turkey/` hem `core`'un soyut sözleşmelerine (yukarı akış) hem `countries/tr/`'nin verisine (aşağı akış) bağımlıdır; ne `core` ne de `countries/tr` bu paketi bilir.

## Çalıştırma / Doğrulama

```bash
# Repo kökünden — motora gerçek Provider nesnelerini bağlar ve bir workflow çalıştırır:
python -c "
from pathlib import Path
from core.engine.plugin_engine import PluginEngine
from plugins.turkey.registration import TurkeyPluginRegistrar

engine = PluginEngine(Path('.'))
engine.load_all()
registrar = TurkeyPluginRegistrar()
registrar.register(engine)
print(registrar.overtime_workflow.execute('fazla mesai zamanaşımı').body)
"
```

## Katmanlar ve SOLID Eşlemesi

| Katman | Dosyalar | Sorumluluk (SRP) | Öne çıkan SOLID notu |
|---|---|---|---|
| **`paths.py`** | 1 | Bu paketin verisini nerede bulacağını bilir | Tek kaynak — yol hesaplama başka hiçbir yerde tekrarlanmaz |
| **`manifest.py`** | 1 | Plugin Manifest — bu kod paketinin kimliği | — |
| **`config/`** | Country Config | `country.config.yaml`'ı tipli nesneye çevirir | `load_country_config(parser=...)` — parser enjekte edilebilir (DIP) |
| **`parser/`** | YAML/markdown ayrıştırma | Sadece ayrıştırır, yorumlamaz | `FileParser` Protocol'ü ile ISP — dar arayüz |
| **`sources/`** | Legal Source Registry | Hukuki otorite kataloğu | — |
| **`citations/`** | Atıf mantığı | 4 ayrı sınıf: statute/case format, risk, provenance | Her sınıf tek metod ailesi — birleşik bir "God Citation" sınıfı yok |
| **`adapters/`** | Dış sistem sınırları | Yargıtay/Resmi Gazete/Mevzuat — her biri kendi dosyasında | Liskov: `is_available()`/`search()` her adapter'da aynı davranır (dürüstçe `False`/`NotImplementedError`) |
| **`mcp/`** | MCP bağlama config'i + client seam'i | `UnavailableMcpClient` bir Null Object — gerçek client Liskov ile yer değiştirebilir | Open/Closed: gerçek transport eklendiğinde çağıran kod değişmez |
| **`providers/`** | Citation/Search/Document Provider implementasyonları | `citations/`+`sources/`+`adapters/`'ı **composition** ile birleştirir | Inheritance değil composition — DIP + SRP |
| **`tools/`** | Provider'ları adlandırılmış callable'lara çevirir | Tool Registry capability_id karşılığı | — |
| **`rag/`** | Yerel `knowledge/*.md` üzerinde anahtar-kelime tabanlı retrieval | Embedding/vector DB YOK — dürüstçe belirtilmiş | — |
| **`prompts/`** | Retrieval + atıf + guardrail notunu birleştirir | Her konu kendi assembler sınıfı | Open/Closed: yeni konu = yeni sınıf, mevcut sınıf değişmez |
| **`workflow/`** | Üst düzey orkestrasyon (`OvertimeQaWorkflow`) | Yalnızca `core.contracts` soyutlamalarına bağımlı | DIP'in en net örneği — constructor injection, `new` çağrısı yok |
| **`registration.py`** | Plugin Registration | Her şeyi inşa eder (composition root) + `engine.providers.attach_instance(...)` ile motora bağlar | Open/Closed: `plugins/germany/registration.py` eklemek bu dosyayı değiştirmez |

## Dürüstlük İlkesi (bu paket boyunca tutarlı)

`adapters/`, `mcp/`, ve `providers/document_provider.py`'deki her "bağlı değil" durumu **gerçek**tir — `countries/tr/capabilities.yaml`'daki `partial`/`not_supported` beyanlarıyla birebir örtüşür. Hiçbir yerde sahte bir "başarılı" sonuç üretilmez; bağlantısızlık `False`/`NotImplementedError`/`available=False` olarak açıkça yüzeye çıkar.

## Bilinçli sınırlar

- Gerçek ağ çağrısı (Yargıtay/Resmi Gazete/Mevzuat'a canlı bağlantı) bu pakette **yoktur** — `adapters/` ve `mcp/client.py` bunun için hazır bir sızdırmaz sınır (seam) sağlar, ama gerçek HTTP/MCP istemcisi ayrı bir iştir.
- `rag/` klasik (embedding tabanlı) bir RAG değildir — bkz. `rag/__init__.py` docstring'i.
- Test altyapısı (pytest) yok; bu paket gerçek `countries/tr/` verisine karşı canlı çalıştırılarak doğrulanmıştır (bkz. bu paketin commit mesajı).
