# MCP Entegrasyon Rehberi

## Tool sözleşmesi

Her tool `BaseMcpTool` sınıfından türemeli ve aşağıdakileri yayınlamalıdır:

- benzersiz `name`
- kullanıcıya dönük `description`
- JSON Schema biçiminde `input_schema`
- `execute(arguments)` içinde MCP uyumlu `content` ve `structuredContent` sonucu

`TurkeyMcpToolServer.list_tools()` tool tanımlarını, `call_tool(name, arguments)` çağrı sonucunu verir.

## Yeni tool ekleme

1. `plugins/turkey/mcp/tools/` altında bir modül oluşturun.
2. `BaseMcpTool` alt sınıfı tanımlayın.
3. Girdi tiplerini `input_schema` ile zorunlu alanlar ve `additionalProperties: false` kullanarak belirtin.
4. Tool dış sisteme erişiyorsa `McpClient` benzeri istemciyi constructor üzerinden alın.
5. Tool modülünü tek başına test edin; registry otomatik keşfeder.

## Canlı kaynaklar

Canlı arama tool’ları transport, kimlik doğrulama, timeout, retry, rate limit ve denetim kaydı politikasını barındıran bir `McpClient` implementasyonu gerektirir. Erişim yoksa `ConnectionError` döndürün; sonuç uydurmayın. Kaynak verisini hukuki otorite veya güncellik bakımından doğrulanmış saymayın; sonuçta provenance ve inceleme ihtiyacını taşıyın.

## Güvenlik

- Kimlik bilgilerini tool argümanlarında veya loglarda taşımayın.
- Kullanıcı girdisini URL, shell, SQL veya HTML bağlamına doğrudan koymayın.
- Tool çıktısını boyut, süre ve hata sınırlarıyla kontrol edin.
- Gönderme, filing veya veri değiştiren işlemleri açık insan onayı olmadan uygulamayın.
