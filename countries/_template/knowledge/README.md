# `knowledge/` — Vertical Başına Ülkeye Özgü İçerik

Her alt dizin bir Core Vertical'ın adını taşır (ör. `employment-legal/`, `corporate-legal/`) ve o vertical'ın skill'lerinin ihtiyaç duyduğu, ülkeye özgü **test/formül/takvim/kontrol listesi** içeriğini barındırır — bugün bu içerik doğrudan SKILL.md'lere gömülüydü (ör. ABD için "29 U.S.C. §207(e) formülü").

## Kural

Bir dosya buraya eklendiğinde, karşılık gelen Core Vertical'ın `extension-points.yaml`'ında bu içeriğin hangi extension point'i karşıladığı **açıkça eşlenmelidir**. Eşlenmeyen bir knowledge dosyası, hiçbir skill tarafından okunmayan ölü içeriktir.

## Opsiyonel: Guardrail Overlay'leri

`<vertical>/overlays/<fragment_id>.md` — bir Core guardrail fragment'ının (bkz. `core/shared/guardrail-fragments/`) üzerine, bu ülkeye özgü **ek** bağlam. Fragment'ın güvenlik özünü asla zayıflatamaz, yalnızca ekler.

*(Bu commit itibarıyla boş — içerik `countries/us` ve `countries/tr` inşa edilirken eklenecek.)*
