# Türkiye — Citation Provider

Bkz. sözleşme: [`core/engine/providers/citation-provider.interface.md`](../../../core/engine/providers/citation-provider.interface.md)

## formatStatuteCitation

**Kalıp:** `[Kanun No] sayılı [Kanun Adı] m.[Madde No]`
**Örnekler:**
- `4857 sayılı İş Kanunu m.41` — fazla mesai
- `4857 sayılı İş Kanunu m.29` — toplu işten çıkarmada bildirim
- `6098 sayılı Türk Borçlar Kanunu m.112` — genel borçlar hükümleri

## formatCaseCitation

**Kalıp:** `Yargıtay [Daire No]. Hukuk Dairesi, [Esas No] E., [Karar No] K., [Tarih] T.`
**Örnek:** `Yargıtay 9. Hukuk Dairesi, 2021/1234 E., 2022/5678 K., 15.03.2022 T.`

## getProvenanceTagVocabulary

| Etiket | Kaynak açıklaması | Canlı araç sonucu gerektirir mi? |
|---|---|---|
| `[Yargıtay]` | Yargıtay karar arama sistemi (resmî/kamuya açık) | evet |
| `[Resmi Gazete]` | Resmî Gazete yayın metni | evet |
| `[mevzuat.gov.tr]` | Mevzuat Bilgi Sistemi | evet |
| `[Lexpera]` / `[Kazancı]` | Ücretli içtihat/mevzuat araştırma platformları (kuruluysa) | evet |

## getHighRiskPinpointPatterns

| Kalıp adı | Açıklama | Örnek |
|---|---|---|
| `madde-fikra` | Madde içindeki fıkra/bent numarası uydurma riski yüksek | "m.41/2" içindeki "/2" |
| `esas-karar-no` | Yargıtay Esas/Karar numaraları — model tarafından sıkça hatalı hatırlanır | "2021/1234 E." |
| `kanun-no-karisikligi` | Benzer konulu kanunların numara karışıklığı (ör. İş Kanunu 4857 ile Borçlar Kanunu 6098) | — |

## classifyCitationRisk — kural özeti

Esas/Karar numarası içeren veya madde/fıkra düzeyinde spesifik olan her atıf `high` risk taşır; genel kanun adı düzeyi atıflar `medium`; kurum adı referansları `low`.

*Not: Bu içerik genel bilgi amaçlıdır ve bir TR hukuk danışmanı incelemesinden geçmemiştir — bkz. migration planındaki "Country Plugin Trust Review" gerekliliği. Üretim kullanımından önce bir avukat tarafından doğrulanmalıdır.*
