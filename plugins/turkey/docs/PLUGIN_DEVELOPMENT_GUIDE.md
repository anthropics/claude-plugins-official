# Turkey Plugin Geliştirme Rehberi

## İlkeler

- Bir modül tek sorumluluk taşımalıdır; HTTP, belge ayrıştırma ve hukuki yorum aynı sınıfta birleşmez.
- Dış sınırlar Protocol/soyut sözleşme ile enjekte edilir.
- Bağlantısı olmayan bir sistem başarı sonucu üretmez; erişilemezlik açıkça yüzeye çıkar.
- Hukuki analizler kaynak, belirsizlik ve avukat incelemesi ihtiyacını taşır.

## Geliştirme akışı

1. Yeni yeteneğin katmanını belirleyin: parser, provider, RAG, MCP tool veya workflow.
2. Önce dar bir sözleşme yazın; somut uygulamayı sözleşmeye göre oluşturun.
3. Dış istemciyi constructor ile enjekte edin; modül içinde ağ istemcisi oluşturmayın.
4. İlgili `plugins/turkey/tests/test_*.py` dosyasında unit testi ekleyin.
5. Sözleşmeler arası akış varsa entegrasyon testi ekleyin.
6. `python3 -m unittest discover -s plugins/turkey/tests -t . -v` komutunu çalıştırın.

## Katman seçimi

- **Provider:** dış hukuk kaynağı veya belge/durum sistemi.
- **Parser:** disk üzerindeki formatı metin/nesneye dönüştürme.
- **RAG:** parse edilmiş belgeyi chunk, embedding ve vector store ile indexleme.
- **MCP tool:** JSON Schema girdili, tek amaçlı kullanıcı çağrılabilir işlem.
- **Workflow/prompt:** birden fazla sözleşmeyi kullanıcıya dönük akışta birleştirme.

## İnceleme listesi

- Yeni bağımlılık isteğe bağlı mı ve hata mesajı açıklayıcı mı?
- Girdi şeması, sınır durumları ve başarısız bağlantı test edildi mi?
- Kullanıcı kontrollü metin HTML/komut/SQL yüzeyine aktarılıyorsa güvenli mi?
- Live-source sonucu ile yerel/model kaynaklı sonuç ayırt ediliyor mu?
