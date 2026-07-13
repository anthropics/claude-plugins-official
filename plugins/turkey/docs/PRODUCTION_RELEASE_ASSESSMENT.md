# Production Release Değerlendirmesi

Tarih: 2026-07-13  
Karar: **Production release için henüz uygun değil.**

## Release öncesi blokajlar

1. Resmî hukuk kaynakları için canlı, yetkilendirilmiş ve test edilmiş MCP/HTTP istemcileri yoktur.
2. Qdrant, FAISS, pgvector ve Milvus sınıfları entegrasyon sözleşmesi sağlar; üretim driver, bağlantı, migration ve dayanıklılık implementasyonu yoktur.
3. Paketlenmiş bağımlılık/lockfile, CI, lint/type-check ve yayın pipeline’ı yoktur.
4. Kimlik bilgisi yönetimi, erişim kontrolü, audit log, telemetry, rate limit ve incident runbook eksiktir.
5. Hukuki kaynak güncelliği, provenance saklama, retention ve insan inceleme operasyonları için production politikası tanımlanmamıştır.

## Geçiş kriterleri

- Seçilen her resmi kaynak için yetkili erişim, timeout/retry, hata bütçesi ve canlı sözleşme testi
- Seçilen embedding modeli ve vector DB için yük/geri yükleme, yedekleme, şifreleme ve veri saklama politikası
- CI üzerinde unit/integration/plugin/provider/tool/RAG/prompt testleri, lint ve type-check
- Secret yönetimi, RBAC, audit logging ve veri sınıflandırma kontrolleri
- Hukuk ekibince onaylanmış kaynak doğrulama ve avukat inceleme prosedürü
- Staging ortamında hata/performans ve adversarial girdi testleri

Bu kriterler tamamlanana kadar paket yalnızca geliştirme veya kontrollü pilot ortamında kullanılmalıdır.
