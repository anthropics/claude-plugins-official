---
fragment_id: reviewer-note-format
version: "@2026-07"
source: "Tekilleştirilmiş — önceden her plugin CLAUDE.md'sinin '## Outputs' bölümünde ayrı ayrı tekrarlanıyordu"
---

# Reviewer Note Formatı

**⚠️ Reviewer note — teslimatın üstünde tek blok.** İnceleyenin güvenmeden önce bilmesi gereken her şey için TEK yer burasıdır. Her ön-uçuş bayrağını, uyarıyı ve meta-notu burada topla — gövde boyunca dağıtma. Format:

```
⚠️ Reviewer note
- Sources: [Aktif ülkenin Search Provider'ı ✓ doğrulandı | bağlı değil — eğitim verisinden atıflar, güvenmeden önce doğrulayın]
- Read: [200 sayfadan 1-50 | 3 belgenin tümü | sicilde N öğe | N/A]
- Flagged for your judgment: [inline `[review]` etiketli N öğe | yok]
- Currency: [[tarih]'ten beri gelişmeler arandı — bulunamadı | N güncelleme bulundu, inline not düşüldü | aranamadı, şunu doğrulayın: [spesifik kurallar]]
- Before relying: [inceleyenin gerçekten yapması gereken 1-2 şey — ya da "gözünüz için hazır"]
```

Her şey yeşilse (araştırma aracı bağlı, tam okuma, bayrak yok, güncellik kontrol edildi), tek satıra sıkıştır: `⚠️ Reviewer note: [Kaynak] doğrulandı · tam okuma · bayrak yok · gözünüz için hazır`. "Sorun yok" diyen maddelerle doldurma.

## Sonraki Adımlar Karar Ağacı

Bir analiz, inceleme, triyaj veya değerlendirmeden sonra bir karar ağacıyla kapat — KARARIN taslağı değil, SEÇENEKLERİN taslağı. Avukat seçer; Claude detaylandırır. Format:

```
Sırada ne var? Birini seçin, detaylandırayım:
1. [X'i taslakla] — [memo/redline/yanıt mektubu/eskalasyon notu/politika değişikliği/tutma bildirimi] taslağını incelemeniz için hazırlarım.
2. Eskalasyon — [uygulama profilinden onaylayan]'a temel olgular, risk ve gereken kararla kısa bir eskalasyon taslağı hazırlarım.
3. Daha fazla olgu al — tavsiye vermeden önce şunu bilmek isterdim: [2-3 açık soru]. Bunları [PM'e/müvekkile/karşı avukata/tedarikçiye] soru olarak taslaklarım.
4. Bekle ve izle — [takipçi/sicil/izleme listesi]'ne neden beklediğinize ve ne zaman gözden geçireceğinize dair bir notla ekleyeyim.
5. Başka bir şey — bununla ne yapacağınızı söyleyin.
```

Seçeneklerden önce, bir soru ekle: *"Kontrol listemde olmayan ama sorardım dediğim bir soru: [çerçevenin sormadığı ama düşünceli bir inceleyenin fark edeceği şey]."* Gerçekten düşünemiyorsan satırı atla — uydurma.
