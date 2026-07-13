---
fragment_id: jurisdiction-recognition
version: "@2026-07"
source: "Tekilleştirilmiş — önceden her plugin CLAUDE.md'sinde ayrı ayrı tekrarlanıyordu ('US-centric' varsayımıyla)"
---

# Jurisdiction Recognition

Bir skill'in varsayılan çerçeveleri, testleri, kanunları ve usulleri **aktif ülkenin hukuk sistemine göre değişir** (bkz. Country Config → `legal_family`). Kullanıcı, dava/mesele, veya olgular aktif olandan farklı bir yargı yetkisini içerdiğinde bunu tanı ve buna göre davran — bir yargı yetkisinin doktrinini sessizce başka bir yargı yetkisinin olgularına uygulama.

1. **Tespit et.** Uygulama profilinin yargı yetkisi ayak izini kontrol et. Meselenin olgularını kontrol et (geçerli hukuk, tarafların konumu, ürünün satıldığı yer, etkilenen kişilerin bulunduğu yer). Bunlardan biri aktif ülkeden farklıysa, aktif ülkenin çerçevesi uygulanmayabilir.
2. **Değerlendir.** Skill'in bu yargı yetkisi için bir çerçevesi (bir Country Plugin bağlaması) var mı? Varsa kullan.
3. **Yoksa:** Açıkça söyle: *"Bu analiz [aktif ülke]'nin çerçevesini kullanıyor ([test/kanun]). Siz [yargı yetkisi]'ndesiniz, orada hukuk farklı. Buradaki doktrini uygulamak, doğru görünen ama yanlış bir cevap verir."*
4. **Karar ağacında bir sonraki adımı sun:**
   - **Geçerli standardı ara.** Bir Search Provider bağlıysa "[yargı yetkisi] [konu] standardı" araması yap, bulguları `[verify against primary source]` etiketiyle raporla.
   - **Bir uzmana yönlendir.** "[Yargı yetkisi] uygulamacısı bu kararı vermeli. Ona sorulacak spesifik soru: [...]."
   - **Boşluğu bayrakla ve bir uyarıyla devam et.** "Başlangıç yapısı olarak [aktif ülke] çerçevesini çalıştıracağım, ama her sonuç `[[aktif ülke] framework — verify against [yargı yetkisi] law]` etiketli olacak."
5. **Asla yanlış yargı yetkisinin hukukunu kullanarak güvenli bir cevap üretme.** Güvenli-ve-yanlış, belirsiz-ve-bayraklı'dan daha kötüdür.

## Legal Family Farklılıkları — Kavramsal Karşılıksızlık

Bazı kavramların (ör. common-law'a özgü keşif/discovery, jüri talimatları) civil-law veya karma-Şeriat etkili sistemlerde **hiç karşılığı olmayabilir**. Bu durumda skill, yapay bir eşdeğer icat etmez — [Coverage Report](../../core/engine/plugin-loader/COVERAGE_REPORT_FORMAT.md)'ta `not_applicable` olarak açıkça işaretler.
