---
fragment_id: cross-skill-severity-floor
version: "@2026-07"
source: "Tekilleştirilmiş — önceden her plugin CLAUDE.md'sinde ayrı ayrı tekrarlanıyordu"
---

# Cross-Skill Severity Floor

Bir skill bir şiddet derecesi taşıyan bir bulgu ürettiğinde ve başka bir skill bu bulguyu tükettiğinde, alt akıştaki (downstream) skill üst akıştaki (upstream) şiddeti bir TABAN olarak taşır. Üst akışta 🔴 olarak derecelendirilmiş bir bulgu, alt akışta şunu belirtmeden "tavsiye edilir" seviyesine düşürülemez: *"Üst akış bunu [X] olarak derecelendirdi. [Sebep] nedeniyle [Y]'ye düşürüyorum."* Sessiz düşürme, inceleyen avukatın göremeyeceği bir çelişkidir.

**Kanonik ölçek:** 🔴 Bloklayıcı / 🟠 Yüksek / 🟡 Orta / 🟢 Düşük. Vertical'a özgü herhangi bir ölçek buna eşlenir. Eşleme belirsizse, YUKARI yuvarla.

## Öznel Hukuki Kararlarda Karar Duruşu

Bu vertical'daki bir skill öznel bir hukuki değerlendirmeyle (bu bir P0 engelleyici mi, bu iddia kanıtlanabilir mi, bu risk yeni mi) karşılaştığında ve cevap belirsizse, skill **geri alınabilir hatayı** tercih eder: spesifik satırı `[review]` ile inline bayrakla ve belirsizliği orada not düş. Öznel bir eşiğin karşılanmadığına sessizce karar verme; ilkeyi vaaz eden ayrı bir uyarı paragrafı yayma. `[review]` bayrağı MEKANİZMANIN KENDİSİDİR — avukat listeyi daraltır, yapay zeka değil. Az-bayraklamak tek yönlü bir kapı; çok-bayraklamak avukatın 30 saniyede kapattığı iki yönlü bir kapıdır. Varsayılan, iki yönlü kapıya doğrudur.
