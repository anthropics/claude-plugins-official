# Yeni Ülke Ekleme Rehberi

1. `countries/_template/` dizinini `countries/<iso-kod>/` olarak kopyalayın ve tüm `[PLACEHOLDER]` alanlarını doldurun.
2. Ülke yapılandırması, yetenek matrisi, hukuk kaynağı kaydı, MCP bağları ve provider dokümanlarını ülke verisiyle tamamlayın.
3. `plugins/turkey/` yapısını `plugins/<iso-kod>/` için referans alın; hiçbir ülke bilgisini `core/` altına taşımayın.
4. Citation, search ve document provider’larını core Protocol’lerine uygun biçimde yazın.
5. Kaynak provider’larını tek modüllü otomatik keşif düzeniyle ekleyin.
6. Yerel hukuk belgeleri için parser/RAG yapılandırması ve ülkeye özgü test verisi ekleyin.
7. MCP tool’ları JSON Schema ile tanımlayın; canlı kaynaklar için açık erişilebilirlik kontrolü koyun.
8. Unit, provider, RAG, tool, prompt, plugin ve entegrasyon testlerini ülke paketi altında oluşturun.
9. Country README’sine kapsam, varsayımlar, veri kaynakları, bağlantı sınırları ve doğrulama komutunu yazın.

Bir ülkenin production’a aday olması için hukuk kaynağı kapsamı, güncellik sorumluluğu, gizlilik/yerelleştirme kuralları ve avukat inceleme süreci açıkça belgelenmelidir.
