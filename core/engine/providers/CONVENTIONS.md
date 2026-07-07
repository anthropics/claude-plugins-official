# Provider Arayüzleri — Ortak Konvansiyonlar

Bu doküman, `citation-provider.interface.md`, `search-provider.interface.md` ve `document-provider.interface.md` dosyalarının **hepsinin paylaştığı** kuralları tek bir yerde toplar. Her üç arayüz dosyası bu konvansiyonlara *referans verir*, tekrar etmez — amaç, kod tekrarının dokümantasyon seviyesindeki karşılığını (aynı kuralın üç yerde birbirinden bağımsız, birbirinden sapabilecek şekilde yazılmasını) önlemektir. Bir konvansiyon burada değişirse, üç arayüz dosyası da otomatik olarak güncel kalır — ayrı ayrı düzenlenmeleri gerekmez.

---

## 1. Arayüz Versiyonlama

Her Provider arayüzü, tarihe dayalı bir versiyon taşır: `<provider-adı>@YYYY-MM` (örn. `citation-provider@2026-07`). Bu, reponun `managed-agent-cookbooks` altında zaten kullandığı `agent_toolset_20260401` tarih-versiyonlama geleneğiyle tutarlıdır.

- Bir arayüze **geriye uyumlu olmayan** bir değişiklik yapıldığında (bir metodun imzası değişir, zorunlu bir alan eklenir), versiyon artırılır ve önceki versiyon bir süre daha desteklenir.
- Bir Country Plugin, `capabilities.yaml` içinde hangi arayüz versiyonuna karşı test edildiğini beyan eder (`citation-provider: "@2026-07"` gibi).
- Plugin Loader, bir Core Vertical'ın istediği versiyon ile Country Plugin'in sağladığı versiyon uyuşmuyorsa bunu sessizce yok saymaz — Coverage Report'ta açıkça "version mismatch" olarak işaretler.

## 2. Dependency Injection İlkesi

Bu dizindeki hiçbir dosya, hiçbir somut Country Plugin'i (`countries/tr`, `countries/us`, ...) isimden bile olsa referans vermez. Bir Core Vertical skill'i şu şekilde yazılır:

> "Aktif ülkenin Search Provider'ını kullanarak ara." (✅ arayüze bağımlı)

Şu şekilde **yazılmaz**:

> "CourtListener MCP'sini kullanarak ara." (❌ somut implementasyona bağımlı — hardcode)

Somut implementasyonun *hangisi* olduğu, Plugin Loader tarafından çalışma zamanında çözümlenir ve skill'e "enjekte edilir" (bkz. `core/engine/plugin-loader/` — ayrı commit). Bu, geleneksel yazılımdaki constructor/setter injection'ın, dosya-okuma tabanlı bir çalışma zamanında (LLM prompt yürütmesi) karşılığıdır.

## 3. Hata ve Fallback Semantiği (üç geçerli sonuç)

Her Provider metodu çağrıldığında üç geçerli sonuç vardır — ikisi değil:

1. **`RESULT`** — İstenen veri başarıyla döner.
2. **`NOT_AVAILABLE`** — Bu ülke için bu yetenek hiç implemente edilmemiş veya bağlı connector yanıt vermiyor. Bu **sessizce yutulamaz**; çağıran skill bunu kullanıcıya açıkça bildirmek zorundadır (reponun mevcut "no silent supplement" ve "no silent no-ops" ilkelerinin Provider seviyesindeki karşılığı).
3. **`DEGRADED`** — Kısmi/düşük güvenilirlikli sonuç döner (ör. ücretsiz katmandan geldi, doğrulanmamış). Sonuçla birlikte bir `confidence`/`tier` alanı taşınmalıdır.

Hiçbir Provider implementasyonu, `NOT_AVAILABLE` durumunu `RESULT` gibi göstererek "boş ama başarılı" bir yanıt üretemez.

## 4. Provenance Etiket Sözlüğü — Taban Kural

Core, evrensel geçerliliği olan şu etiketleri sabitler (hiçbir Country Plugin bunları değiştiremez):

- `[model knowledge — verify]` — eğitim verisinden gelen her şeyin varsayılan etiketi.
- `[user provided]` — kullanıcının yapıştırdığı/verdiği içerik.
- `[web search — verify]` — genel web araması sonucu.

Her Country Plugin, bunlara **ek olarak**, kendi bağladığı somut kaynaklara özgü etiketler tanımlayabilir (ör. TR için `[Yargıtay]`, `[Resmi Gazete]`; ABD için `[CourtListener]`, `[Westlaw]`). Bu ek etiketler `citation-provider.interface.md` → `getProvenanceTagVocabulary()` sözleşmesi üzerinden bildirilir. Bir etiket, yalnızca o oturumda o kaynaktan **gerçekten** sonuç geldiğinde kullanılabilir — bu kural hiçbir ülke tarafından gevşetilemez.

## 5. Salt-Okunur İlkesi

Üç arayüzün üçü de **salt okunurdur** (durum sorgular, eylem gerçekleştirmez). Bir belgeyi imzalatmak, bir dilekçe dosyalamak, bir mesaj göndermek gibi yazma eylemleri bu arayüzlerin kapsamı dışındadır ve Tool Registry'nin en-az-yetki katmanlamasına (reader/analyzer/writer) tabidir — bu commit'in kapsamında değildir.

## 6. Conformance (Uyumluluk) Beyanı

Bir Country Plugin, bu arayüzlerden birini "implemente ettiğini" iddia edebilmek için üç dosya değil, **tek bir beyan dosyası** üretir: `countries/<code>/capabilities.yaml`. Bu dosya, her metod için `full` / `partial` / `not_supported` durumunu beyan eder. Kısmi ya da desteklenmeyen bir metod, sessizce eksik bırakılamaz — açıkça beyan edilmek zorundadır.
