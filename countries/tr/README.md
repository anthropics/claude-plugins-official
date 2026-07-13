# Türkiye Ülke Plugin'i (`countries-tr`)

Bu, `claude-for-legal` marketplace'inin **ilk yeni-pazar ülke plugin'idir** (bkz. kök `CLAUDE.md` ve mimari tasarım oturumu). Core Vertical'lara (şu an: `employment-legal`) Türk hukuk sistemine özgü içerik ve bağlamalar sağlar.

## Kurulum

```
/plugin install countries-tr@claude-for-legal
/plugin install employment-legal@claude-for-legal
```

Kurulum sırası önemli değildir; her iki plugin de bağımsız kurulabilir. Aktivasyon adımı (Plugin Loader'ın `active-country.yaml`'ı yazması) şu an manuel bir adımdır — otomatik aktivasyon skill'i henüz eklenmemiştir (bkz. gelecek dalga).

## Bu paket ne sağlıyor

| Bileşen | Durum |
|---|---|
| Country Config | ✓ Tam (`country.config.yaml`) |
| Legal Source Registry | ✓ Tam (`legal-sources/legal-source-registry.tr.yaml`) |
| Citation Provider | ✓ Tam |
| Search Provider | △ Kısmi — hedef kaynaklar belgelenmiş, çalışan bir MCP sunucusu henüz yok |
| Document Provider | △ Kısmi — e-imza/UYAP bağlamaları belgelenmiş, çalışan bir MCP sunucusu henüz yok |
| `employment-legal` Knowledge Pack | ✓ Tam ilk taslak — **TR hukuk danışmanı incelemesi bekliyor** |

Tam kapsam tablosu için `capabilities.yaml`'a bakın.

## ⚠️ Önemli — Üretim Kullanımından Önce

Bu paketteki her önemli hukuki iddia `[verify]` etiketlidir ve genel bilgiye dayanmaktadır — repo'nun kendi "Country Plugin Trust Review" gerekliliği burada henüz karşılanmamıştır. Gerçek bir Türk iş hukuku avukatı tarafından doğrulanmadan müvekkil/çalışan işine güvenilmemelidir.

## Kapsam

Şu an yalnızca `employment-legal` vertical'ı için içerik sağlanmıştır. Diğer vertical'lar (`commercial-legal`, `corporate-legal`, ...) için TR kapsamı `not_applicable`/eksik olarak işaretlenmemiştir çünkü henüz hiç ele alınmamıştır — bu, gelecekteki bir dalganın işidir.
