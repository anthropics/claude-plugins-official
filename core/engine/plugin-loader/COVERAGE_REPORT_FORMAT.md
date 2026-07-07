---
component: coverage-report
version: "@2026-07"
status: stable
scope: core (ülke bağımsız)
---

# Coverage Report Formatı

## Amaç

Bir kullanıcının "bu ülke plugin'i, kurduğum vertical'ları ne kadar destekliyor?" sorusuna, her `cold-start-interview`/aktivasyon sonrası ve her skill çalıştırıldığında (kısaltılmış biçimde) net bir cevap vermek. Bugünkü "araştırma connector'ı bağlı mı?" ön-uçuş kontrolünün ülke-seviyesine genellenmiş hâlidir.

## Tam Format (aktivasyon sonrası gösterilir)

```
📋 Kapsam Raporu — <Country Plugin adı> × kurulu vertical'lar

| Vertical          | Citation | Search | Document | Genel   |
|-------------------|----------|--------|----------|---------|
| employment-legal   | ✓ full   | ✓ full | △ partial| Partial |
| commercial-legal   | ✓ full   | ✓ full | ✓ full   | Full    |
| law-student        | —        | —      | —        | N/A     |

Partial/N/A olan her satır için:
- employment-legal → Document Provider yalnızca e-imza durumunu destekliyor,
  CLM meta verisi bu ülke için henüz bağlı değil.
- law-student → bu vertical'ın temel kavramı (bar exam) bu ülkede
  karşılıksız; kapsam dışı bırakıldı, yapay bir eşdeğer üretilmedi.
```

## Kısa Format (her skill çalıştırıldığında, reviewer note'a eklenir)

Tek satıra sıkıştırılır ve mevcut "⚠️ Reviewer note" bloğunun **Sources:** satırına eklenir (yeni bir banner icat edilmez):

```
⚠️ Reviewer note
- Sources: [Yargıtay ✓ verified | ülke: TR, vertical kapsamı: partial — Document Provider sınırlı]
```

## Durum Kodları

| Kod | Anlam |
|---|---|
| `full` | Vertical'ın `extension-points.yaml`'daki her talebi ülke tarafından karşılanıyor |
| `partial` | Bazı metodlar karşılanıyor, bazıları `not_supported` |
| `missing` | Ülke plugin'i bu vertical için hiçbir beyan içermiyor |
| `not_applicable` (N/A) | Ülke, bu vertical'ı kavramsal olarak desteklemediğini açıkça beyan etmiş (bkz. Legal Family farklılıkları) |

`missing` ve `not_applicable` birbirinden **kasıtlı olarak** ayrılır: `missing` bir eksiklik/gelecek iş kalemidir, `not_applicable` bilinçli bir kapsam kararıdır (ör. bir common-law kavramının civil-law ülkesinde zorlanarak uydurulmaması).

## Üretim Kuralı

Coverage Report **hiçbir zaman** Plugin Loader tarafından "her şey yolunda" göstermek için iyimser yuvarlanamaz. `partial` bir satır, hangi spesifik metodun eksik olduğunu isimlendirmek zorundadır — reponun mevcut "Don't pad with bullets that all say 'no issues'" ilkesinin tersi yönde bir zorunluluk: burada "no issues" demek için gerçekten hiç issue olmaması gerekir.

## Değişiklik Günlüğü

- `@2026-07` — İlk yayın (bu commit).
