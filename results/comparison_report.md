# Neural Simplification of Banking Regulations — Comparison Report

**Generated:** 2026-04-25 13:58

---

## Model Comparison

| Model | ROUGE-1 | ROUGE-2 | ROUGE-L | BLEU |
|-------|---------|---------|---------|------|
| TextRank (Baseline) | 0.7647 | 0.6212 | 0.7647 | 0.2534 |
| TF-IDF (Baseline) | 0.7647 | 0.6212 | 0.7647 | 0.2534 |
| Neural (mT5 + LoRA) | 0.0348 | 0.0 | 0.0348 | 0 |
| Zero-Shot LLM | 0.2414 | 0.1865 | 0.2381 | 0.035 |

---

## Error Analysis

### Hallucination Detection

- **Average Hallucination Score:** 0.0429
- **Number Hallucinations:** 0 samples
- **Term Preservation Rate:** 1.0
- **Word Overlap:** 0.4842

### Faithfulness Analysis

- **Average Faithfulness Score:** 0.5458
- **TF-IDF Similarity:** 0.5231
- **Low Faithfulness Count:** 0 samples

---

## Sample Predictions (Neural Model)

### Example 1

**Karmaşık:** + [Banka Dışı Mali Kuruluş Verileri](/Veri/Index/70) - [Faktoring](/Veri/Detay/163) - [Finansal Kiralama](/Veri/Detay/164) - [Finansman Şirketleri](/Veri/Detay/165) - [Varlık Yönetim](/Veri/Detay/166)

**Referans:** Banka Dışı Mali Kuruluş Verileri - Faktoring - Finansal Kiralama - Finansman Şirketleri - Varlık Yönetim Bağımsız Denetim Raporları VERİ YAYIMLAMA TAKVİMİ Kuruluşlar

**Tahmin:** <extra_id_0>ları

### Example 2

**Karmaşık:** + [Banka Dışı Mali Kuruluş Verileri](/Veri/Index/70) - [Faktoring](/Veri/Detay/163) - [Finansal Kiralama](/Veri/Detay/164) - [Finansman Şirketleri](/Veri/Detay/165) - [Varlık Yönetim](/Veri/Detay/166)

**Referans:** Banka Dışı Mali Kuruluş Verileri - Faktoring - Finansal Kiralama - Finansman Şirketleri - Varlık Yönetim Bağımsız Denetim Raporları VERİ YAYIMLAMA TAKVİMİ Kuruluşlar

**Tahmin:** <extra_id_0>ları

### Example 3

**Karmaşık:** + [Kanunlar](/Mevzuat/Liste/49) + [Bankacılık Kanununa İlişkin Düzenlemeler](/Mevzuat/Liste/50) + [Banka Kartları ve Kredi Kartları Kanununa İlişkin Düzenlemeler](/Mevzuat/Liste/51) + [Finansal Kirala

**Referans:** Kanunlar Bankacılık Kanununa İlişkin Düzenlemeler Banka Kartları ve Kredi Kartları Kanununa İlişkin Düzenlemeler Finansal Kiralama, Faktoring, Finansman ve Tasarruf Finansman Şirketleri Kanununa İlişk

**Tahmin:** <extra_id_0>leri
