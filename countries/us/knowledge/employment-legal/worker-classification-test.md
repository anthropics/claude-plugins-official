# US — Worker Classification Test (employment-legal / worker-classification)

*Kaynak: `employment-legal/skills/worker-classification/SKILL.md` içindeki mevcut ABD-özel içeriğin bu commit'te birebir çıkarılmış hâli.*

## ABC Testi

Çoğu eyalette (ve federal bazı bağlamlarda) bir işçinin bağımsız yüklenici mi yoksa çalışan mı olduğu **ABC testi** ile belirlenir — üç unsurun **tümü** karşılanmalıdır (aksi halde çalışan sayılır):

- **A** — İşçi, hizmetin ifasında hem sözleşme kapsamında hem de fiilen işverenin kontrolü ve yönlendirmesinden bağımsızdır.
- **B** — İşçi, işverenin olağan iş akışı dışında bir iş yapar.
- **C** — İşçi, aynı nitelikte bağımsız olarak kurulmuş bir ticaret, meslek veya işte mutat olarak yer alır.

## Eyalete Özgü Kodifikasyon — Kaliforniya

Kaliforniya'da ABC testi **Cal. Lab. Code §§2775/2776/2783** ile kodifiye edilmiştir; bu maddeler ayrıca meslek-bazlı istisnalar (B2B istisnası dahil) içerir. Eyalete özgü alt-fıkra numaraları **en yüksek uydurma riski** taşıyan pinpoint atıflardır (bkz. [`../../providers/citation-provider.us.md`](../../providers/citation-provider.us.md) → `getHighRiskPinpointPatterns`).

## Yürüyen Bir Angajmanın Sınıflandırılması — Dur ve Yönlendir

Angajman **zaten mevcutsa** (herhangi bir biçimde, herhangi bir süredir), bu bir planlama egzersizi değildir — şu geri ödeme sorumluluklarını içeren bir sorumluluk değerlendirmesidir: geriye dönük ödeme (fazla mesai, yemek/dinlenme primleri), ödenmemiş işveren-tarafı bordro vergisi, reddedilmiş yardım uygunluğu, işsizlik ve işçi tazminatı geriye dönük maruziyeti, eyalet cezaları (CA'da **PAGA**), **IRS §530 rahatlatma** analizi ve — sıkı-test yargı yetkilerinde devam eden çalışma varsa — bir günü daha çalıştırmaya izin vermenin ileriye dönük maruziyeti.

## Ekstraksiyon Notu

Bu içerik `worker-classification-test` ve `worker-classification-remediation` extension point'lerini karşılar.
