// BankSimplify — Frontend Application

const API_BASE = '';
let currentOffset = 0;

// --- Tab Navigation ---
function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));

    document.getElementById(`tab-${tabName}`).classList.add('active');
    document.getElementById(`panel-${tabName}`).classList.add('active');

    if (tabName === 'dashboard') loadStats();
    if (tabName === 'dataset') loadParagraphs(0);
}

// --- Character Count ---
function updateCharCount() {
    const text = document.getElementById('input-text').value;
    document.getElementById('char-count').textContent = `${text.length} karakter`;
}

// --- Load Sample Text ---
function loadSample() {
    const samples = [
        `5411 sayılı Bankacılık Kanununun 43 üncü maddesi uyarınca, bankaların konsolide ve konsolide olmayan bazda hesaplayacakları sermaye yeterliliği standart oranının yüzde sekizden az olamayacağı hükmü gereğince, kredi riskine esas tutarın hesaplanmasında risk ağırlıklı varlıklar ve gayri nakdi krediler ile taahhütlerin ilgili risk ağırlıkları ile çarpılması suretiyle bulunan tutarların toplamı esas alınır. Bu çerçevede, konsolide olmayan bazda sermaye yeterliliği standart oranının hesaplanmasında, bankanın bilanço içi varlıkları, gayri nakdi kredileri ve taahhütleri ile türev finansal araçlarına ilişkin kredi riskine esas tutarlar dikkate alınmaktadır.`,
        `5464 sayılı Banka Kartları ve Kredi Kartları Kanununun 4 üncü maddesi ve Banka Kartları ve Kredi Kartları Hakkında Yönetmeliğin 11 inci maddesinin birinci fıkrası çerçevesinde yapılan değerlendirme neticesinde; kart çıkaran kuruluşların, kart hamillerinin talebi olmaksızın kredi kartı limitlerini artırmalarının mümkün olmadığı ve limit artırımı işlemlerinin ancak kart hamilinin açık talebi üzerine yapılabileceği hüküm altına alınmıştır.`,
        `Bankaların iç sistemleri kapsamında, iç denetim, iç kontrol ve risk yönetimi birimlerinin bağımsızlığının sağlanması, bu birimlerin doğrudan yönetim kuruluna veya denetim komitesine bağlı olarak faaliyet göstermesi, söz konusu birimlerde görev yapan personelin mesleki yeterliliğe sahip olması ve düzenli eğitim programlarına katılması zorunluluğu, Bankacılık Düzenleme ve Denetleme Kurumu tarafından çıkarılan ilgili yönetmelik hükümleri çerçevesinde düzenlenmiştir.`
    ];
    document.getElementById('input-text').value = samples[Math.floor(Math.random() * samples.length)];
    updateCharCount();
}

// --- Simplify ---
async function simplifyText() {
    const text = document.getElementById('input-text').value.trim();
    if (text.length < 30) {
        alert('Lütfen en az 30 karakterlik bir metin girin.');
        return;
    }

    const btn = document.getElementById('btn-simplify');
    const loader = document.getElementById('loader');
    const results = document.getElementById('results-container');

    btn.disabled = true;
    loader.classList.add('active');
    results.innerHTML = '';

    try {
        const res = await fetch(`${API_BASE}/api/simplify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, models: ['textrank', 'tfidf'] })
        });
        const data = await res.json();
        renderResults(data.results);
    } catch (err) {
        results.innerHTML = `<div class="card" style="color: var(--accent-rose);">❌ Hata: ${err.message}</div>`;
    } finally {
        btn.disabled = false;
        loader.classList.remove('active');
    }
}

function renderResults(results) {
    const container = document.getElementById('results-container');
    container.innerHTML = results.map(r => {
        const modelLabels = {
            textrank: { name: 'TextRank', badge: 'badge-textrank', icon: '📗' },
            tfidf: { name: 'TF-IDF', badge: 'badge-tfidf', icon: '📘' },
            neural: { name: 'Neural (mT5)', badge: 'badge-neural', icon: '🧠' },
            zeroshot: { name: 'Zero-Shot LLM', badge: 'badge-zeroshot', icon: '⚡' }
        };
        const label = modelLabels[r.model] || { name: r.model, badge: '', icon: '📄' };

        const faithClass = r.faithfulness_score >= 0.5 ? 'good' : r.faithfulness_score >= 0.3 ? 'warn' : 'bad';
        const hallClass = r.hallucination_score <= 0.2 ? 'good' : r.hallucination_score <= 0.5 ? 'warn' : 'bad';
        const termClass = r.term_preservation_rate >= 0.8 ? 'good' : r.term_preservation_rate >= 0.5 ? 'warn' : 'bad';

        return `
        <div class="result-card">
            <div class="result-header">
                <div class="result-model-name">
                    ${label.icon} ${label.name}
                    <span class="result-badge ${label.badge}">${r.model.toUpperCase()}</span>
                </div>
                <span style="font-size: 12px; color: var(--text-muted);">
                    ${r.original_length} → ${r.simplified_length} karakter
                </span>
            </div>
            <div class="result-body">
                <div class="result-text">${escapeHtml(r.simplified)}</div>
                <div class="result-metrics">
                    <div class="metric-item">
                        <div class="metric-value" style="color: var(--accent-cyan);">${(r.compression_ratio * 100).toFixed(0)}%</div>
                        <div class="metric-label">Sıkıştırma</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value ${faithClass}">${(r.faithfulness_score * 100).toFixed(0)}%</div>
                        <div class="metric-label">Sadakat</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value ${hallClass}">${(r.hallucination_score * 100).toFixed(0)}%</div>
                        <div class="metric-label">Halüsinasyon</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value ${termClass}">${(r.term_preservation_rate * 100).toFixed(0)}%</div>
                        <div class="metric-label">Terim Koruma</div>
                    </div>
                </div>
            </div>
        </div>`;
    }).join('');
}

// --- Analyze ---
async function analyzeText() {
    const text = document.getElementById('input-text').value.trim();
    if (text.length < 30) {
        alert('Lütfen en az 30 karakterlik bir metin girin.');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        const data = await res.json();
        renderAnalysis(data);
    } catch (err) {
        console.error('Analysis error:', err);
    }
}

function renderAnalysis(data) {
    const el = document.getElementById('analysis-result');
    const circumference = 2 * Math.PI * 34;
    const maxScore = 5;
    const normalizedScore = Math.min(data.complexity_score / maxScore, 1);
    const offset = circumference * (1 - normalizedScore);

    const levelColors = {
        'Çok Karmaşık': 'var(--accent-rose)',
        'Karmaşık': 'var(--accent-amber)',
        'Orta': 'var(--accent-blue)',
        'Basit': 'var(--accent-emerald)',
    };
    const color = levelColors[data.complexity_level] || 'var(--accent-blue)';

    el.innerHTML = `
    <div class="complexity-gauge">
        <div class="gauge-ring">
            <svg width="80" height="80" viewBox="0 0 80 80">
                <circle class="gauge-bg" cx="40" cy="40" r="34"/>
                <circle class="gauge-fill" cx="40" cy="40" r="34"
                    style="stroke: ${color}; stroke-dasharray: ${circumference}; stroke-dashoffset: ${offset}"/>
            </svg>
            <div class="gauge-value" style="color: ${color}">${data.complexity_score}</div>
        </div>
        <div class="gauge-info">
            <h3 style="color: ${color}">${data.complexity_level}</h3>
            <p>${data.word_count} kelime · ${data.sentence_count} cümle · Jargon: ${(data.jargon_density * 100).toFixed(1)}%</p>
        </div>
    </div>`;
    el.style.display = 'block';
}

// --- Dashboard Stats ---
async function loadStats() {
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        const data = await res.json();

        document.getElementById('stat-docs').textContent = data.data.raw_documents;
        document.getElementById('stat-paras').textContent = data.data.extracted_paragraphs;
        document.getElementById('stat-train').textContent = data.data.train_pairs;
        document.getElementById('stat-jargon').textContent = (data.data.avg_jargon_density * 100).toFixed(1) + '%';
        document.getElementById('stat-complexity').textContent = data.data.avg_complexity_score.toFixed(1);
        document.getElementById('stat-test').textContent = data.data.test_pairs;

        // Model comparison
        renderModelComparison(data.models);
    } catch (err) {
        console.error('Stats error:', err);
    }
}

function renderModelComparison(models) {
    const container = document.getElementById('model-comparison');
    const hasData = models.baseline && Object.keys(models.baseline).length > 0;

    if (!hasData) return;

    let rows = '';
    for (const [name, result] of Object.entries(models.baseline)) {
        const m = result.metrics;
        rows += `<tr>
            <td><span class="result-badge badge-${name}">${name.toUpperCase()}</span></td>
            <td>${m.rouge1?.toFixed(4) || '—'}</td>
            <td>${m.rouge2?.toFixed(4) || '—'}</td>
            <td>${m.rougeL?.toFixed(4) || '—'}</td>
            <td>${m.bleu?.toFixed(4) || '—'}</td>
        </tr>`;
    }

    if (models.neural && models.neural.metrics) {
        const m = models.neural.metrics;
        rows += `<tr>
            <td><span class="result-badge badge-neural">NEURAL</span></td>
            <td>${m.rouge1?.toFixed(4) || '—'}</td>
            <td>${m.rouge2?.toFixed(4) || '—'}</td>
            <td>${m.rougeL?.toFixed(4) || '—'}</td>
            <td>${m.bleu?.toFixed(4) || '—'}</td>
        </tr>`;
    }

    container.innerHTML = `
    <table class="data-table">
        <thead><tr><th>Model</th><th>ROUGE-1</th><th>ROUGE-2</th><th>ROUGE-L</th><th>BLEU</th></tr></thead>
        <tbody>${rows}</tbody>
    </table>`;
}

// --- Dataset Browser ---
async function loadParagraphs(offset = 0) {
    currentOffset = Math.max(0, offset);
    try {
        const res = await fetch(`${API_BASE}/api/paragraphs?limit=20&offset=${currentOffset}`);
        const data = await res.json();

        const tbody = document.getElementById('paragraphs-body');
        if (data.paragraphs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-muted); padding: 40px;">
                Henüz paragraf yok. Veri toplama pipeline'ını çalıştırın.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.paragraphs.map(p => `
        <tr>
            <td style="font-size: 12px; color: var(--text-muted); white-space: nowrap;">${p.id}</td>
            <td style="white-space: nowrap;">${p.source_doc}</td>
            <td class="truncate" title="${escapeHtml(p.complex_text)}">${escapeHtml(p.complex_text.slice(0, 120))}…</td>
            <td style="color: var(--accent-amber);">${(p.metadata.jargon_density * 100).toFixed(1)}%</td>
            <td style="color: var(--accent-purple);">${p.metadata.complexity_score}</td>
            <td><button class="btn btn-secondary" style="padding: 6px 12px; font-size: 12px;"
                onclick="useForSimplification('${escapeAttr(p.complex_text)}')">Kullan</button></td>
        </tr>`).join('');

        document.getElementById('page-info').textContent =
            `${currentOffset + 1}–${Math.min(currentOffset + 20, data.total)} / ${data.total}`;
    } catch (err) {
        console.error('Paragraphs error:', err);
    }
}

function useForSimplification(text) {
    document.getElementById('input-text').value = text;
    updateCharCount();
    switchTab('simplify');
}

// --- Utilities ---
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function escapeAttr(str) {
    return str.replace(/'/g, "\\'").replace(/\n/g, ' ').slice(0, 500);
}

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
    updateCharCount();
});
