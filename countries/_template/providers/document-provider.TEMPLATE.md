# [PLACEHOLDER — Ülke Adı] Document Provider

# core/engine/providers/document-provider.interface.md sözleşmesinin somut
# implementasyon TANIMI.

## Bağlı sistemler

| Yetenek | Somut sistem | Auth türü |
|---|---|---|
| E-imza durumu | [PLACEHOLDER] | [PLACEHOLDER] |
| Dosyalama/tebligat durumu | [PLACEHOLDER] | [PLACEHOLDER] |

## getIrreversibilityFlags — bu ülkede yaygın eylem türleri

| actionType | irreversible | gateRequired | Gerekçe |
|---|---|---|---|
| `[PLACEHOLDER — ör. sign-envelope]` | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |

**Tanımsız bir eylem türü için varsayılan:** `irreversible: true, gateRequired: true` (bkz. arayüz dosyasındaki zorunlu güvenli-varsayılan kuralı).
