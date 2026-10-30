// Exemple de signal ECG pour tester
const exampleSignal = [
    0.98, 0.91, 0.72, 0.46, 0.18, -0.12, -0.38, -0.61, -0.78, -0.89,
    -0.94, -0.93, -0.86, -0.74, -0.58, -0.39, -0.18, 0.03, 0.24, 0.43,
    0.59, 0.72, 0.81, 0.87, 0.89, 0.88, 0.84, 0.77, 0.68, 0.57,
    0.44, 0.31, 0.17, 0.04, -0.08, -0.19, -0.28, -0.35, -0.40, -0.43,
    -0.44, -0.44, -0.42, -0.39, -0.35, -0.31, -0.26, -0.21, -0.16, -0.11,
    -0.06, -0.02, 0.02, 0.05, 0.08, 0.10, 0.12, 0.13, 0.14, 0.14,
    0.14, 0.13, 0.12, 0.11, 0.09, 0.08, 0.06, 0.04, 0.02, 0.00,
    -0.02, -0.04, -0.05, -0.07, -0.08, -0.09, -0.10, -0.10, -0.11, -0.11,
    -0.11, -0.11, -0.10, -0.10, -0.09, -0.08, -0.07, -0.06, -0.05, -0.04,
    -0.03, -0.02, -0.01, 0.00, 0.01, 0.02, 0.03, 0.04, 0.04, 0.05,
    0.05, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06, 0.05, 0.05,
    0.05, 0.04, 0.04, 0.03, 0.03, 0.02, 0.02, 0.01, 0.01, 0.00,
    0.00, -0.01, -0.01, -0.01, -0.02, -0.02, -0.02, -0.02, -0.03, -0.03,
    -0.03, -0.03, -0.03, -0.03, -0.03, -0.03, -0.03, -0.02, -0.02, -0.02,
    -0.02, -0.02, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01, 0.00, 0.00,
    0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,
    0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,
    0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,
    0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00
];

// Charger les statistiques du modèle au démarrage
window.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/model-info');
        const data = await response.json();
        if (data.accuracy) {
            document.getElementById('modelAccuracy').textContent = data.accuracy;
        }
    } catch (error) {
        document.getElementById('modelAccuracy').textContent = 'N/A';
    }
});

function switchTab(tabName) {
    // Cacher tous les contenus
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Désactiver tous les boutons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Activer le tab sélectionné
    document.getElementById(tabName + 'Tab').classList.add('active');
    event.target.classList.add('active');
}

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const text = e.target.result;
        const lines = text.trim().split('\n');
        
        // Prendre la première ligne (ignorer l'en-tête si présent)
        let firstLine = lines[0];
        if (isNaN(firstLine.split(',')[0])) {
            firstLine = lines[1]; // Sauter l'en-tête
        }
        
        document.getElementById('signalInput').value = firstLine;
        switchTab('manual');
        showError('Fichier chargé ! Vérifiez les données et lancez la prédiction.');
    };
    reader.readAsText(file);
}

function generateRandom() {
    const type = document.getElementById('randomType').value;
    let signal = [];
    
    if (type === 'random') {
        // Complètement aléatoire
        for (let i = 0; i < 187; i++) {
            signal.push((Math.random() * 2 - 1).toFixed(2));
        }
    } else if (type === 'normal') {
        // Simulation d'un signal normal (onde sinusoïdale)
        for (let i = 0; i < 187; i++) {
            const t = i / 187;
            const value = Math.sin(t * Math.PI * 2) * 0.5 + Math.random() * 0.1;
            signal.push(value.toFixed(2));
        }
    } else {
        // Simulation d'un signal anormal (avec pics)
        for (let i = 0; i < 187; i++) {
            const t = i / 187;
            let value = Math.sin(t * Math.PI * 2) * 0.5;
            if (i > 80 && i < 100) {
                value += Math.random() * 1.5; // Pic anormal
            }
            signal.push(value.toFixed(2));
        }
    }
    
    document.getElementById('signalInput').value = signal.join(', ');
    switchTab('manual');
}

function loadExample() {
    document.getElementById('signalInput').value = exampleSignal.join(', ');
    switchTab('manual');
}

function clearInput() {
    document.getElementById('signalInput').value = '';
    document.getElementById('results').style.display = 'none';
    document.getElementById('error').style.display = 'none';
}

function parseSignal(text) {
    // Remplacer les virgules, points-virgules et retours à la ligne par des espaces
    const cleaned = text.replace(/[,;\n]/g, ' ');
    // Extraire les nombres
    const values = cleaned.split(/\s+/).filter(v => v.trim() !== '').map(v => parseFloat(v));
    return values;
}

async function predict() {
    const input = document.getElementById('signalInput').value;
    const errorDiv = document.getElementById('error');
    const resultsDiv = document.getElementById('results');
    const predictBtn = document.getElementById('predictBtn');
    
    // Cacher les messages précédents
    errorDiv.style.display = 'none';
    resultsDiv.style.display = 'none';
    
    if (!input.trim()) {
        showError('Veuillez entrer un signal ECG');
        return;
    }
    
    // Parser le signal
    let signal;
    try {
        signal = parseSignal(input);
    } catch (e) {
        showError('Format invalide. Utilisez uniquement des nombres séparés par des virgules, espaces ou retours à la ligne.');
        return;
    }
    
    if (signal.length !== 187) {
        showError(`Le signal doit contenir exactement 187 valeurs. Vous en avez fourni ${signal.length}.`);
        return;
    }
    
    // Désactiver le bouton pendant le traitement
    predictBtn.disabled = true;
    predictBtn.textContent = 'Analyse en cours...';
    
    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ signal: signal })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showError(data.error || 'Erreur lors de la prédiction');
            return;
        }
        
        displayResults(data, signal);
        
        // Sauvegarder dans l'historique
        history.add(signal, data);
        
    } catch (error) {
        showError('Erreur de connexion au serveur: ' + error.message);
    } finally {
        predictBtn.disabled = false;
        predictBtn.textContent = 'Lancer la prédiction';
    }
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = '❌ ' + message;
    errorDiv.style.display = 'block';
}

function displayResults(data, signal) {
    const resultsDiv = document.getElementById('results');
    
    // Afficher la classe prédite et la confiance
    document.getElementById('predictedClass').textContent = data.class_name;
    document.getElementById('confidence').textContent = (data.confidence * 100).toFixed(2) + ' %';
    
    // Dessiner le signal
    drawSignal(signal);
    
    // Afficher les probabilités
    displayProbabilities(data.probabilities);
    
    resultsDiv.style.display = 'block';
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
}

function drawSignal(signal) {
    const canvas = document.getElementById('signalChart');
    const ctx = canvas.getContext('2d');
    
    // Ajuster la taille du canvas
    canvas.width = canvas.offsetWidth;
    canvas.height = 250;
    
    const width = canvas.width;
    const height = canvas.height;
    const padding = 40;
    const graphWidth = width - 2 * padding;
    const graphHeight = height - 2 * padding;
    
    // Trouver min et max pour normaliser
    const min = Math.min(...signal);
    const max = Math.max(...signal);
    const range = max - min;
    
    // Effacer le canvas
    ctx.clearRect(0, 0, width, height);
    
    // Fond
    ctx.fillStyle = '#f8f9fa';
    ctx.fillRect(0, 0, width, height);
    
    // Grille
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 10; i++) {
        const y = padding + (graphHeight / 10) * i;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
    }
    
    // Dessiner le signal
    ctx.strokeStyle = '#c1121f';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    signal.forEach((value, index) => {
        const x = padding + (index / (signal.length - 1)) * graphWidth;
        const y = padding + graphHeight - ((value - min) / range) * graphHeight;
        
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    
    ctx.stroke();
    
    // Axes
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height - padding);
    ctx.lineTo(width - padding, height - padding);
    ctx.stroke();
}

function displayProbabilities(probabilities) {
    const container = document.getElementById('probabilities');
    container.innerHTML = '';
    
    Object.entries(probabilities).forEach(([className, prob]) => {
        const barDiv = document.createElement('div');
        barDiv.className = 'prob-bar';
        
        const percentage = (prob * 100).toFixed(2);
        
        barDiv.innerHTML = `
            <div class="prob-label">${className}</div>
            <div class="prob-bar-container">
                <div class="prob-bar-fill" style="width: ${percentage}%">
                    ${percentage}%
                </div>
            </div>
        `;
        
        container.appendChild(barDiv);
    });
}
