# Turkey Plugin

`plugins/turkey/`, `countries/tr/` spesifikasyonunu çalıştırılabilir Python bileşenlerine dönüştüren Türkiye hukuk pluginidir. Hukuki araştırma sonuçları ve analizleri taslaktır; kaynaklar doğrulanmadan hukuki görüş veya işlem dayanağı olarak kullanılmamalıdır.

## Kapsam

- Türkiye ülke yapılandırması, kaynak kataloğu, atıf biçimlendirme ve iş günü hesabı
- UYAP, Resmî Gazete, Mevzuat Bilgi Sistemi, Yargıtay, Danıştay, AYM ve KVKK için genişletilebilir provider katmanı
- PDF, DOCX, HTML ve TXT belgeleri için provider bağımsız RAG altyapısı
- Değiştirilebilir embedding sağlayıcısı ve Qdrant, FAISS, pgvector, Milvus uyumlu vector-store sözleşmesi
- Dokuz bağımsız MCP tool: kaynak arama, kanun karşılaştırma, atıf üretimi, karar/risk analizi, madde arama ve karar özeti

## Mimari

| Katman | Sorumluluk | Ana giriş noktası |
|---|---|---|
| `config/`, `sources/` | `countries/tr/` YAML verisini tipli nesnelere çevirir | `load_country_config()` |
| `citations/` | Kanun/karar atıf biçimi ve risk sınıflaması | `TurkishCitationProvider` |
| `providers/` | Core provider sözleşmelerini uygular | `TurkeyPluginRegistrar` |
| `providers/legal_sources/` | Her hukuk kaynağı için tek modüllü provider | `discover_legal_source_providers()` |
| `parser/` | Yerel belge ayrıştırma; ağ/provider bağımlılığı yoktur | `LegalDocumentParserRegistry` |
| `rag/` | Chunking, embedding ve vector-store ile belge retrieval | `LegalRag` |
| `mcp/tools/` | Bağımsız MCP tool tanımları | `TurkeyMcpToolServer` |
| `workflow/`, `prompts/` | Provider’ları kullanıcıya dönük iş akışlarında birleştirir | `OvertimeQaWorkflow` |

## Kurulum ve doğrulama

Bu paket Python 3.11+ ve YAML yapılandırması için `PyYAML` kullanır. Core engine’i yükleyen üretim akışları ayrıca `jsonschema` gerektirir.

```bash
python3 -m unittest discover -s plugins/turkey/tests -t . -v
```

Mevcut test paketi unit, provider, RAG, tool, prompt, plugin ve entegrasyon seviyelerini kapsar.

## Provider’lar

Provider’lar `LegalSourceProvider` sözleşmesini uygular: `source_id`, `source_name`, `source_type`, `is_available()` ve `search(query)`. Yeni bir kaynak eklemek için `providers/legal_sources/` altında `BaseLegalSourceProvider` alt sınıfı içeren bir Python modülü ekleyin. Registry modülü bunu otomatik keşfeder; kayıt dosyasını değiştirmeniz gerekmez.

Mevcut provider’lar canlı HTTP/MCP bağlantısı yapılandırılmadığında erişilemez durum döndürür veya açık hata verir; sahte arama sonucu üretmezler.

## RAG kullanımı

```python
from pathlib import Path
from plugins.turkey.parser.legal_document import LegalDocumentType
from plugins.turkey.rag import LegalRag

rag = LegalRag()
rag.ingest(Path("karar.txt"), LegalDocumentType.COURT_DECISION)
hits = rag.retrieve("kişisel veri", top_k=3)
```

Varsayılanlar `HashEmbeddingProvider` ve `InMemoryVectorStore`dur. Üretimde model-backed bir embedding sağlayıcısını ve seçilen veritabanı adaptörünü constructor injection ile verin. PDF ayrıştırma için `pypdf`, DOCX ayrıştırma için `python-docx` isteğe bağlı bağımlılıktır.

## MCP tool kullanımı

```python
from plugins.turkey.mcp import TurkeyMcpToolServer

server = TurkeyMcpToolServer()
tools = server.list_tools()
result = server.call_tool(
    "turkey_citation_generator",
    {"kind": "statute", "instrument": "4857 sayılı İş Kanunu", "section": "41"},
)
```

Her tool MCP tool metadata’sı (`name`, `description`, `inputSchema`) ve `content` / `structuredContent` sonuç yapısı yayınlar. Canlı kaynak arama tool’ları enjekte edilmiş bir `McpClient` gerektirir.

## Sınırlar

- Canlı UYAP, mahkeme, Resmî Gazete veya Mevzuat bağlantıları bu repoda yapılandırılmış değildir.
- Qdrant, FAISS, pgvector ve Milvus için ortak arayüz vardır; üretim sürücüleri ve bağlantı yönetimi ayrıca uygulanmalıdır.
- Karar özeti ve risk/karar analiz tool’ları ilk geçiş sinyal üretir; avukat incelemesi gerektirir.

## Belgeler

- [Plugin geliştirme rehberi](docs/PLUGIN_DEVELOPMENT_GUIDE.md)
- [Yeni ülke ekleme rehberi](docs/ADDING_COUNTRY_GUIDE.md)
- [MCP entegrasyon rehberi](docs/MCP_INTEGRATION_GUIDE.md)
- [Kod kalite raporu](docs/CODE_QUALITY_REPORT.md)
- [Production release değerlendirmesi](docs/PRODUCTION_RELEASE_ASSESSMENT.md)
