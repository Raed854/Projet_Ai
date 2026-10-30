// Système d'historique des prédictions
class PredictionHistory {
    constructor() {
        this.predictions = JSON.parse(localStorage.getItem('ecg_history') || '[]');
        this.maxSize = 10;
    }

    add(signal, result) {
        const entry = {
            timestamp: new Date().toISOString(),
            signal: signal,
            predicted_class: result.predicted_class,
            class_name: result.class_name,
            confidence: result.confidence
        };

        this.predictions.unshift(entry);
        
        // Limiter la taille
        if (this.predictions.length > this.maxSize) {
            this.predictions = this.predictions.slice(0, this.maxSize);
        }

        localStorage.setItem('ecg_history', JSON.stringify(this.predictions));
    }

    getAll() {
        return this.predictions;
    }

    clear() {
        this.predictions = [];
        localStorage.removeItem('ecg_history');
    }

    get(index) {
        return this.predictions[index];
    }
}

const history = new PredictionHistory();

function showHistory() {
    const historyList = history.getAll();
    
    if (historyList.length === 0) {
        alert('Aucune prédiction dans l\'historique');
        return;
    }

    let html = '<div class="history-popup"><div class="history-content">';
    html += '<h3>Historique des prédictions</h3>';
    html += '<button onclick="closeHistory()" class="close-btn">✕</button>';
    
    historyList.forEach((item, index) => {
        const date = new Date(item.timestamp);
        html += `
            <div class="history-item" onclick="loadFromHistory(${index})">
                <div class="history-date">${date.toLocaleString('fr-FR')}</div>
                <div class="history-result">${item.class_name}</div>
                <div class="history-confidence">${(item.confidence * 100).toFixed(2)}%</div>
            </div>
        `;
    });
    
    html += '<button onclick="clearHistory()" style="margin-top: 20px; background: #c1121f;">Effacer l\'historique</button>';
    html += '</div></div>';
    
    document.body.insertAdjacentHTML('beforeend', html);
}

function closeHistory() {
    const popup = document.querySelector('.history-popup');
    if (popup) popup.remove();
}

function loadFromHistory(index) {
    const item = history.get(index);
    document.getElementById('signalInput').value = item.signal.join(', ');
    closeHistory();
    alert('Signal chargé depuis l\'historique !');
}

function clearHistory() {
    if (confirm('Êtes-vous sûr de vouloir effacer tout l\'historique ?')) {
        history.clear();
        closeHistory();
    }
}

// Exporter l'historique
function exportHistory() {
    const data = history.getAll();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ecg_history.json';
    a.click();
}
