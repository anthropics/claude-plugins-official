---
fragment_id: large-input-output
version: "@2026-07"
source: "Tekilleştirilmiş — önceden her plugin CLAUDE.md'sinde ayrı ayrı tekrarlanıyordu"
---

# Büyük Girdi ve Büyük Çıktı

## Büyük Girdi

Bir skill bir belgeyi, mesele dosyasını, üretim setini veya veri odasını okuduğunda ve girdi BÜYÜKSE (kabaca >50 sayfa, >100 belge, >10K satır veya bir alt kümeyle çalıştığından şüphelenmene neden olan herhangi bir şey), sessizce kısmi bir okumadan güvenli bir çıktı üretme. Başarısızlık modu: model bağlam dolana kadar alır, keser ve 80-200. sayfaların okunmadığına dair inceleyen avukata hiçbir sinyal vermeden sözleşmenin yalnızca ilk %40'ını okuyan bir memo üretir.

- **Ne okuduğunu bil.** Kapsamı Reviewer Note'un **Read:** satırında kaydet — ör. `200 sayfadan 1-50; 51-200 atlandı`. Gövdede ayrıca bir kapsam ifadesi koyma.
- **Önceliklendir.** Bir sözleşme için: tanımları, temel yükümlülükleri, süreyi, feshi, sorumluluğu, tazminatı, IP'yi, veriyi, gizliliği ve geçerli hukuk bölümlerini önce oku. Bir üretim seti için: okumadan önce tarihe, saklayıcıya ve türe göre triyaj et. Bir sicil için: durum veya tarih aralığına göre filtrele.
- **Destekleniyorsa böl.** Büyük işleri parçalara ayır, her birini işle ve topla. Toplama herhangi bir bulguyu düşürüyorsa bayrakla.
- **Bir ekip olman gerektiğinde söyle.** "Bu 500 belgelik bir veri odası. Bu ölçekte ilk-geçiş bir inceleme tek-ajan işi değil, bir belge-inceleme platformu işidir. İlk [N]'yi triyaj edip gerisini bir platform çalışması için bayraklayacağım."
- **Her şeyi okuduğunu asla iddia etme.** Kısmi bir okumadan güvenli bir sonuç, "bir örnek okudum ve bulduklarım şunlar; okumadıklarım şunlar"dan daha kötüdür.

## Büyük Çıktı

Kullanıcı "tüm iş akışlarını çalıştır", "her belgeyi incele", "her şeyi işle" veya bir turda sığmayacak daha fazla çıktı üretecek herhangi bir şey istediğinde, önce kapsamı belirle. Boyutu tahmin et ("her biri ~100 satır olan kabaca 15 iş akışı — yaklaşık 1.500 satır"), bir seçim sun ("3-5'inde ayrıntılı bir geçiş, 15'inin tümünde hızlı bir geçiş, ya da 15'in tümünü partiler halinde yapabilirim — hangisini istersiniz?") ve cevabı bekle. Bir turda sığmayan bir plana bağlanmak, kullanıcının göremeyeceği sessiz bir kesintiye yol açar.
