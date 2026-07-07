# Türkiye — Document Provider

Bkz. sözleşme: [`core/engine/providers/document-provider.interface.md`](../../../core/engine/providers/document-provider.interface.md)

## Bağlı sistemler

| Yetenek | Somut sistem | Auth türü |
|---|---|---|
| E-imza durumu | e-İmza / KamuSM nitelikli elektronik sertifika sağlayıcıları | Sertifika tabanlı |
| Tebligat durumu | UYAP e-Tebligat | Baro/avukat portalı yetkilendirmesi |
| Dosyalama durumu | UYAP e-Dosya (avukat portalı) | Baro/avukat portalı yetkilendirmesi |

## getIrreversibilityFlags — bu ülkede yaygın eylem türleri (employment-legal kapsamı)

| actionType | irreversible | gateRequired | Gerekçe |
|---|---|---|---|
| `send-termination-letter` | true | true | Fesih bildirimi tebliğ edildiğinde feshin geçerlilik süreci başlar (İş Kanunu m.19 savunma alma yükümlülüğü dahil). |
| `send-offer-letter` | false | false | Aday kabul etmeden önce revize edilebilir. |
| `sign-ibraname` (ibra sözleşmesi) | true | true | İmzalandığında işçinin alacaklarından feragati yürürlüğe girer — Yargıtay'ın ibranameye ilişkin sıkı şekil şartları vardır (6098 sayılı TBK m.420). |

**Tanımsız bir eylem türü için varsayılan:** `irreversible: true, gateRequired: true`.

*Not: Bu içerik genel bilgi amaçlıdır ve bir TR hukuk danışmanı incelemesinden geçmemiştir.*
