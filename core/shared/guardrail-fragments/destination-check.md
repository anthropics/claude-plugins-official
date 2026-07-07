---
fragment_id: destination-check
version: "@2026-07"
source: "Tekilleştirilmiş — önceden commercial-legal, employment-legal, ip-legal, ai-governance-legal CLAUDE.md dosyalarında ayrı ayrı tekrarlanıyordu"
---

# Destination Check

A `PRIVILEGED & CONFIDENTIAL` (veya `{{country.privilegeHeader}}`) başlığı bir etikettir, bir kontrol değildir. Herhangi bir çıktı üretmeden veya göndermeden önce nereye gittiğini kontrol et:

- Kullanıcı bir hedef adlandırdıysa (bir kanal, bir dağıtım listesi, bir karşı taraf, "herkes"), sor: bu, ayrıcalık/gizlilik çemberinin içinde mi?
- Ayrıcalığı **kaldıran** hedefler: herkese açık kanallar, şirket geneli listeler, karşı taraf/karşı avukat, tedarikçiler, müşteriler (iş ürünü için), avukat-müvekkil ilişkisi ve onun temsilcileri dışındaki herkes.
- Hedef çemberin dışında görünüyorsa: bunu bayrakla. "X kanalı için bir sürüm istediniz — bu şirket geneli bir kanal, bu da bu analizdeki iş-ürünü korumasını kaldırır. Şunlardan birini verebilirim: (a) yalnızca hukuk için ayrıcalıklı sürüm, (b) daha geniş kanal için sadeleştirilmiş sürüm, (c) her ikisi. Hangisini istersiniz?"
- Hedef belirsizse: sor.
- **Asla** sessizce ayrıcalıklı bir başlık uygulayıp sonra belgeyi başlığın koruyamayacağı bir yere göndermeye yardım etme.

## Ülke Uyarlama Notu

`{{country.privilegeHeader}}` yer tutucusu, aktif ülkenin Country Config'indeki `privilege_doctrine` alanından çözülür. `privilege_doctrine.exists: false` olan bir ülkede, başlık metni doktrini var gibi göstermez — `fallback_header` alanındaki dürüst, abartısız metin kullanılır (bkz. [`country-config.schema.yaml`](../../core/engine/providers/country-config.schema.yaml)).
