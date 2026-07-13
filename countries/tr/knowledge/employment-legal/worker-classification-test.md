# TR — Worker Classification Test (employment-legal / worker-classification)

*Bu içerik genel bilgi amaçlıdır, bir TR iş hukuku danışmanı tarafından doğrulanmamıştır.*

## ABD'nin ABC Testinin TR Karşılığı Yoktur

Türk hukukunda ABD'nin ABC testi gibi kodifiye, üç-unsurlu bir test **yoktur** — bu, `jurisdiction-recognition` guardrail'inin tam olarak uyarmak için var olduğu türden bir kavramsal karşılıksızlık örneğidir. Bunun yerine TR hukuku, iş sözleşmesinin **unsurlarına** bakar:

## İş Sözleşmesinin Unsurları

4857 sayılı İş Kanunu m.8 ve 6098 sayılı Türk Borçlar Kanunu (hizmet sözleşmesi hükümleri, m.393 vd.) uyarınca bir ilişkinin iş sözleşmesi (işçi-işveren) mi yoksa bağımsız hizmet ilişkisi (TBK'nın eser/vekalet sözleşmesi hükümleri) mi olduğu üç unsura bakılarak değerlendirilir `[verify]`:

1. **İş görme** — bir işin (fiziksel veya fikri emek) yerine getirilmesi.
2. **Ücret** — karşılığında bir bedel ödenmesi.
3. **Bağımlılık (bağımlılık ilişkisi)** — işverenin talimat verme yetkisi, çalışma saat/yerinin belirlenmesi, işçinin işverenin organizasyonuna dahil olması. **Bağımlılık unsuru, ayırt edici unsurdur** — iş görme ve ücret hem iş sözleşmesinde hem bağımsız hizmet ilişkisinde bulunabilir.

## Muvazaa (Gizli/Örtülü İş İlişkisi) Denetimi

Bir ilişkinin sözleşmede "hizmet alım sözleşmesi" veya "bağımsız danışmanlık" olarak adlandırılmasına rağmen fiiliyatta bağımlılık unsurunu taşıması durumunda, SGK ve iş mahkemeleri **muvazaa** tespiti yapabilir `[verify]` — ABD'nin "misclassification" kavramının TR karşılığı. Muvazaa tespiti halinde ilişki baştan itibaren iş sözleşmesi sayılır ve geriye dönük SGK prim farkı, idari para cezası ve kıdem/ihbar tazminatı doğabilir.

## Ekstraksiyon Notu

Bu içerik `worker-classification-test` extension point'ini karşılar. ABD'nin ABC testi ile birebir eşleşme aranmamalıdır — bu, `jurisdiction-recognition` fragment'ının "asla yanlış yargı yetkisinin hukukunu kullanarak güvenli bir cevap üretme" kuralının somut bir uygulamasıdır.
