---
interface: document-provider
version: "@2026-07"
status: stable
implemented-by: countries/<code>/providers/document-provider.<code>.md
conventions: ./CONVENTIONS.md
---

# Document Provider

## Sorumluluk

Dışarıda yönetilen bir hukuki belgenin **durumunu** soyutlar: imza/zarf durumu, dosyalama/tebligat durumu, ve bir eylemin geri döndürülemez olup olmadığı bilgisini verir. Bugünkü DocuSign/Ironclad/UYAP-e-tebligat gibi somut connector'ların yerini alan **tek bir davranış sözleşmesidir**.

Ortak kurallar için bkz. [`CONVENTIONS.md`](./CONVENTIONS.md).

## Bağımlılık yönü

Bir Core Vertical skill'i (ör. `corporate-legal/skills/written-consent/SKILL.md`'nin bugünkü "DocuSign'a gönderme" geri-döndürülemezlik kontrolü) şu şekilde yazılır: *"Aktif ülkenin Document Provider'ı ile bu eylemin geri döndürülemezlik bayrağını sorgula."* Hangi somut sistemin (DocuSign, e-imza/KamuSM, beA, RPVA...) bu isteği karşılayacağı skill metninde asla adlandırılmaz.

## Metod Sözleşmeleri

| Metod | Girdi | Çıktı | Açıklama |
|---|---|---|---|
| `getDocumentStatus(reference)` | `{ documentId: string }` | `{ status: "draft" \| "in-review" \| "final" \| "archived" }` | Genel belge yaşam-döngüsü durumu. |
| `getSignatureStatus(reference)` | `{ envelopeId: string }` | `{ status: "draft" \| "sent" \| "partially_signed" \| "executed" \| "voided" }` | E-imza/zarf durumu. |
| `getFilingStatus(reference)` | `{ docketId: string }` | `{ status: "not_filed" \| "filed" \| "accepted" \| "rejected", filedAt?: string }` | Mahkeme/idari dosyalama veya tebligat durumu. |
| `getIrreversibilityFlags(action)` | `{ actionType: string }` | `{ irreversible: boolean, gateRequired: boolean, reason?: string }` | Bir eylemin (ör. "imzaya gönder", "dosyala") geri döndürülemez olup olmadığını ve dış hukuk müşaviri onay kapısı gerekip gerekmediğini bildirir. |

## Dönüş Semantiği

Bkz. CONVENTIONS §3. `getIrreversibilityFlags()` özel bir durum taşır: eğer bu ülke için bir eylem türü hiç tanımlı değilse (`NOT_AVAILABLE`), çağıran skill bunu **varsayılan olarak `irreversible: true, gateRequired: true`** kabul etmek zorundadır — yani "bilmiyorum" durumu, güvenli tarafta (daha fazla onay isteyen tarafta) hataya düşer. Bu, reponun "under-flagging is a one-way door, over-flagging is a two-way door" ilkesinin Provider seviyesindeki zorunlu karşılığıdır.

## Kapsam Dışı (Non-goals)

- **Yazma/eylem gerçekleştirmez.** Bir belgeyi imzalatmak, dosyalamak, göndermek bu arayüzün kapsamı dışındadır — salt durum sorgulanır (bkz. CONVENTIONS §5). Yazma eylemleri, ayrı ve açıkça yetkilendirilmiş bir "Writer" katmanına aittir (Tool Registry'nin en-az-yetki modeli, bu commit'in kapsamında değil).
- **Belge içeriğini okumaz/yorumlamaz.** Bu, ilgili skill'in ve varsa bir Document Management System connector'ının işidir.

## Uyumluluk Kontrol Listesi (Country Plugin için)

- [ ] `getIrreversibilityFlags()` için en az bu ülkede yaygın olan eylem türleri (imza, dosyalama, tebligat) tanımlanmış.
- [ ] Tanımsız bir eylem türü için varsayılan davranışın güvenli tarafta (`irreversible: true`) olduğu doğrulanmış.
- [ ] Bu üç durum metodundan hiçbiri yazma/eylem gerçekleştiren bir yan etkiye sahip değil.

## Değişiklik Günlüğü

- `@2026-07` — İlk yayın (bu commit).
