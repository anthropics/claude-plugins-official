# United States — Document Provider

Bkz. sözleşme: [`core/engine/providers/document-provider.interface.md`](../../../core/engine/providers/document-provider.interface.md)

## Bağlı sistemler

| Yetenek | Somut sistem | Auth türü |
|---|---|---|
| E-imza durumu | DocuSign / DocuSign CLM | OAuth |
| DMS/CLM meta verisi | iManage, Ironclad | OAuth |
| Dosyalama durumu | *(employment-legal kapsamında bağlı değil — bkz. `capabilities.yaml` → `getFilingStatus: not_supported`)* | — |

## getIrreversibilityFlags — bu ülkede yaygın eylem türleri (employment-legal kapsamı)

| actionType | irreversible | gateRequired | Gerekçe |
|---|---|---|---|
| `send-termination-letter` | true | true | Gönderildikten sonra geri alınamaz; işten çıkarma iddialarında delil teşkil eder. |
| `send-offer-letter` | false | false | Aday kabul etmeden önce revize edilebilir; ancak restrictive covenant içeriyorsa `gateRequired: true` önerilir (skill seviyesinde ayrıca değerlendirilir). |
| `sign-severance-agreement` | true | true | İmzalandığında feragat/ibra hükümleri yürürlüğe girer. |

**Tanımsız bir eylem türü için varsayılan:** `irreversible: true, gateRequired: true` (arayüz sözleşmesindeki zorunlu güvenli-varsayılan kuralı).
