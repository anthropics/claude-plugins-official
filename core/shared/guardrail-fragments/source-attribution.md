---
fragment_id: source-attribution
version: "@2026-07"
source: "Tekilleştirilmiş — önceden her plugin CLAUDE.md'sinde ayrı ayrı tekrarlanıyordu (Commit 15 sırasında, employment-legal'e uygulanırken tespit edildi)"
---

# Source Attribution

Kaynak etiketleri ne yaptığını tanımlar, ne iddia etmek istediğini değil.

- `{{country.citationTagVocabulary}}` (ör. `[CourtListener]`, `[Yargıtay]`) — SADECE atıf, bu oturumda o MCP'nin bir araç sonucunda gerçekten göründüyse.
- `[statute / regulator site]` — SADECE bu oturumda resmî bir kaynaktan metni gerçekten çektiysen.
- `[user provided]` — kullanıcının yapıştırdığı veya bağlantı verdiği.
- `[model knowledge — verify]` — geri kalan her şey. Bu varsayılandır.
- **`[settled — last confirmed YYYY-MM-DD]`** — belirtilen tarihte birincil bir kaynağa karşı kontrol edilmiş, istikrarlı kanun/mevzuat referansları. Tarih önemlidir: "istikrarlı" referanslar değişir. Son kontrol tarihini teyit edemiyorsan bunun yerine `[model knowledge — verify]` kullan — doğrulanmamış bir "settled", tüm atıf sisteminin önlemeye çalıştığı güvenli abartıdır.

Bir atfı "doğru görünüyor" diye yükseltme. Etiket kökeni tanımlar, güveni değil.

## Etiket Sözlüğü — Genel Bakış

Inline etiketler taşıyıcıdır (load-bearing). Skill'ler genelinde tutarlı kullan:

- `[verify]` — okuyucunun güvenmeden önce birincil bir kaynağa karşı doğrulaması gereken bir olgusal iddia (atıf, tarih, süre, eşik, sicil numarası, kural metni). Kaynak eğitim bilgisiyse uzun biçim `[model knowledge — verify]` kullan.
- `[review]` — avukatın vermesi gereken bir karar. Olgusal bir boşluk değil; skill'in bir pozisyon yüzeye çıkardığı ve avukatın karar vermesi gereken bir yer.
- `{{country.citationTagVocabulary}}` / `[statute / regulator site]` / `[user provided]` — bir atfın gerçekte nereden geldiği. Güven değil, köken. Yalnızca atıf o oturumda o kaynakta gerçekten göründüğünde kullan.
- `[VERIFY: …]` / `[UNCERTAIN: …]` — brief taslağı ve kronoloji skill'lerinde spesifik iddiayla birlikte kullanılan `[verify]`'nin genişletilmiş biçimleri. Aynı amaç.

"CourtListener doğrulandı" gibi bir reviewer-note kısaltması, yalnızca bir araştırma aracı atfı gerçekten döndürdüğünde dürüsttür — bu, aracın ne yaptığını tanımlar, skill'in çıktısının ne olduğunu değil. Skill'in çıktısı hiçbir zaman skill'in kendisi tarafından "doğrulanmış" değildir; doğrulayan okuyucudur.

## Alıntılanan Bir Kanunla Anlaşmazlık

Kullanıcı (veya bir mesele belgesi, veya karşı taraf) bir kanunu doğru bulmadığın bir önerme için alıntıladığında ve bağlı bir araştırma aracından veya yüklenen kaynaktan metni alamıyorsan, kanunun ne dediğine dair bir açıklama uydurma. Şunu söyle: "Bu bölüm beklediğimle eşleşmiyor — gerçekte ne kapsadığını söylemek için gerçek metni çekmem gerekir. `[statute unretrieved — verify]`" Sonra ya (a) yapılandırılmış araştırma aracıyla metni al ve alıntıla, (b) kullanıcıdan metni yapıştırmasını iste, ya da (c) avukat incelemesi için bayrakla. Gerçek bir kanunun kendinden emin yanlış bir açıklaması, "bilmiyorum"dan daha kötüdür — bir boşluktan daha zor inanılmazdır ve uydurma otoritenin dosyalanmış iş ürününe nasıl girdiğidir.
