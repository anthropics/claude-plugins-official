# Türkiye Hukuk Plugin'i — Practice Profile Şablonu

## UYARI ⚠️

Bu plugin taslak aşamadır. Tüm hukuki iddialar **[verify]** etiketlidir ve genel bilgiye dayanmaktadır. Gerçek bir Türk iş hukuku avukatı tarafından doğrulanmamıştır.

Hukuki görüş veya işlem dayanağı olarak kullanılmadan ÖNCE, uyumlu bir avukat tarafından incelenmesi gereklidir.

---

## Kullanım

1. Bu şablon, plugin ilk yüklendiğinde şu klasöre kopyalanır:
   ```
   ~/.claude/plugins/config/claude-for-legal/countries-tr/CLAUDE.md
   ```

2. İş hukuku tercihlerinizi bu dosyada tanımlayın.

3. Her skill bu profil verisini okuyor — otomatik olarak uygulanır.

---

## İş Kanunu (Employment-Legal) Bölümü

### Termination Review Defaults

Bir işçi fesih teklifi incelendiğinde, bu varsayılanları kullan:

```yaml
termination:
  # Kıdem tazminatı gerekli mi? (İş Kanunu m.14)
  severance_required: true
  
  # Bildirim süresi (İş Kanunu m.10)
  notice_period_days: 30
  
  # Kanuni sebepler kontrol edilsin mi?
  check_legal_cause: true
  
  # Gözlemci avukat
  reviewing_counsel: "Your Name Here"
  
  # Şirket sektörü (risk tahlili için)
  industry: "Technology"
  
  # Çalışan konumu (Kıbrıs/Türkiye vs.)
  employee_location: "Istanbul, Turkey"
```

### Hiring & Offer Letter Defaults

```yaml
hiring:
  # Denemeli dönem kontrolü
  check_trial_period: true
  
  # Yasaklanmış maddeler (rekabet, sır, vb.)
  check_restrictive_covenants: true
  
  # Kompanzasyon ağırlaştırılı mı?
  check_comp_enforcement: false
  
  # İmza gerektiren sektörler
  requires_signature_on: []
```

### Leave & Deadlines

```yaml
leave:
  # Yıllık izin günü (İş Kanunu m.54)
  annual_leave_days: 20
  
  # Maternite izni gün sayısı
  maternity_leave_days: 120
  
  # Paternite izni gün sayısı
  paternity_leave_days: 5
  
  # İzin taleplerindeki yasal iş günü
  legal_working_days_per_week: 5
```

---

## Kaynak Tercihleri (Legal Sources)

### Atıf Biçimi

Plugin tarafından üretilen tüm atıflar şu sıraya göre kaynak önceliği verir:

1. **Resmî Gazete** (primary source)
2. **Yargıtay Kararları** (case law)
3. **Danıştay Kararları** (admin law)
4. **Kanun Maddeleri** (legal code)

### Erişim Kaynakları

```yaml
sources:
  # Resmî Gazete erişimi
  resmi_gazete: true
  
  # UYAP (Uyuşmazlık Çözüm Aracı Platformu) erişimi
  uyap: true
  
  # Yargıtay karar veritabanı
  yargitay_decisions: true
  
  # Danıştay karar veritabanı
  danistay_decisions: true
```

---

## Hukuki Risk Sınıflaması

Plugin, her tahlili şu kategorilere ayırır:

- 🔴 **RED** — Yüksek risk, avukat onayı gerekli
- 🟡 **YELLOW** — Orta risk, kontrol et
- 🟢 **GREEN** — Düşük risk, standart uygulama

---

## Merkez Ayarları (Coming Soon)

Gelecek versiyonlarda eklenecek:

- [ ] Birden fazla şehir (İstanbul, Ankara, İzmir)
- [ ] Sektöre özgü iş hukuku (Sağlık, Finans, Tarım)
- [ ] Sendika ve toplu iş sözleşmesi (TİS) yükümlülükleri
- [ ] Sosyal Güvenlik (SGK) uyumları

---

## Doğrulama Kontrol Listesi

Plugin'i üretim ortamında kullanmadan ÖNCE:

- [ ] Bir Türk iş hukuku avukatı bu profili inceledi
- [ ] Şirket hukuki görüşü bu ayarlarla uyumlu
- [ ] Erişim kaynakları (UYAP, Resmî Gazete vb.) konfigüre edildi
- [ ] Test durumlarında sonuçlar doğrulandı

---

Sorular veya güncellemeler için: https://github.com/anthropics/claude-for-legal/issues
