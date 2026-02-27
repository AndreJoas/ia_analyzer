function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => section.style.display = 'none');
    document.getElementById(sectionId).style.display = 'block';
    if (sectionId === 'dashboard') {
        loadDashboard();
    }
}

function renderRelatorio(data) {
    const chat = document.getElementById("chatMessages");

    // ===== helpers =====
    const listOrEmpty = (arr) =>
        arr && arr.length ?
        arr.map(item => `<li>${item}</li>`).join("") :
        "<li>—</li>";

    const nivelClass = {
        fraco: "nivel-fraco",
        medio: "nivel-medio",
        forte: "nivel-forte"
    };

    const html = `
        <div class="report-card">

            <h2>📊 Análise do Currículo</h2>

            <div class="score-box">
                <div class="score-circle">${data.score ?? "-"}</div>
                <div class="score-label">Score Geral</div>
                <div class="nivel-badge ${nivelClass[data.nivel_curriculo] || ""}">
                    ${(data.nivel_curriculo || "-").toUpperCase()}
                </div>
            </div>

            <div class="info-grid">
                <p><strong>👤 Nome:</strong> ${data.nome || "-"}</p>
                <p><strong>📧 Email:</strong> ${data.email || "-"}</p>
                <p><strong>📱 Telefone:</strong> ${data.telefone || "-"}</p>
            </div>

            <h3>💼 Experiência</h3>
            <ul>${listOrEmpty(data.experiencia)}</ul>

            <h3>🎓 Educação</h3>
            <ul>${listOrEmpty(data["educacao/formação"] || data.educacao)}</ul>

            <h3>🧠 Habilidades</h3>
            <ul>${listOrEmpty(data.habilidades)}</ul>

            <h3>🌍 Idiomas</h3>
            <ul>${listOrEmpty(data.idiomas)}</ul>

            <h3>💪 Pontos Fortes</h3>
            <ul class="pontos-fortes">
                ${listOrEmpty(data.pontos_fortes)}
            </ul>

            <h3>⚠️ Pontos Fracos</h3>
            <ul class="pontos-fracos">
                ${listOrEmpty(data.pontos_fracos)}
            </ul>

            <h3>🧠 Justificativa do Score</h3>
            <div class="justificativa">
                ${data.justificativa_score || "-"}
            </div>

            <h3>🚀 Sugestões de Melhoria</h3>
            <ul class="sugestoes">
                ${listOrEmpty(data.sugestoes)}
            </ul>

        </div>
    `;

    chat.innerHTML += html;
    chat.scrollTop = chat.scrollHeight;
}


async function uploadNoChat() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        alert("Selecione um PDF.");
        return;
    }

    const chat = document.getElementById("chatMessages");

    chat.innerHTML += `<p><b>Você:</b> 📄 Enviou um currículo...</p>`;

    const formData = new FormData();
    formData.append("file", file);

    showLoading();

    try {
        const response = await fetch("/upload_curriculo", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        renderRelatorio(data.info);

        // chat.innerHTML += `
        //     <div class="bot-msg">
        //         <b>IA:</b><br>
        //         ✅ Score: <b>${data.score}</b><br>
        //         💡 Sugestões:<br>
        //         ${data.sugestoes.map(s => `• ${s}`).join("<br>")}
        //     </div>
        // `;

        chat.scrollTop = chat.scrollHeight;

    } catch (err) {
        console.error(err);
    } finally {
        hideLoading();
    }
}

// Drag and drop functionality
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');

if (uploadArea) {
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type === 'application/pdf') {
            fileInput.files = files;
            // Update UI to show file selected
            uploadArea.innerHTML = `
                <i class="fas fa-check-circle upload-icon" style="color: #28a745;"></i>
                <h3>Arquivo selecionado: ${files[0].name}</h3>
                <p>Clique para alterar ou arraste outro arquivo</p>
                <div class="upload-buttons">
                    <button class="btn-secondary" onclick="document.getElementById('fileInput').click()">Alterar Arquivo</button>
                    <button class="btn-primary" onclick="handleUpload()" id="uploadBtn">Analisar Currículo</button>
                </div>
            `;
        } else {
            alert('Por favor, selecione um arquivo PDF válido.');
        }
    });
}

if (fileInput) {
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            uploadArea.innerHTML = `
                <i class="fas fa-file-pdf upload-icon"></i>
                <h3>Arquivo selecionado: ${file.name}</h3>
                <p>Clique para alterar ou arraste outro arquivo</p>
                <div class="upload-buttons">
                    <button class="btn-secondary" onclick="document.getElementById('fileInput').click()">Alterar Arquivo</button>
                    <button class="btn-primary" onclick="handleUpload()" id="uploadBtn">Analisar Currículo</button>
                </div>
            `;
        }
    });
}

async function loadHistorico() {
    const response = await fetch('/historico');
    const data = await response.json();
    const list = document.getElementById('historicoList');
    list.innerHTML = data.map(item => `
        <div onclick="showModal('${item.id}')">
            <p>Nome: ${item.nome}</p>
            <p>Score: ${item.score}</p>
            <p>Data: ${item.data}</p>
        </div>
    `).join('');
}

async function loadDashboard() {
    const response = await fetch('/historico');
    const data = await response.json();
    const total = data.length;
    const scores = data.map(item => item.score);
    const avg = scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(2) : 0;

    document.getElementById('totalAnalises').textContent = total;
    document.getElementById('scoreMedio').textContent = avg;

    // Gráfico
    const ctx = document.getElementById('scoreChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map((_, i) => `Análise ${i+1}`),
            datasets: [{
                label: 'Score',
                data: scores,
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

function showModal(id) {
    fetch(`/historico`)
        .then(res => res.json())
        .then(data => {
            const item = data.find(d => d.id === id);
            if (!item) return alert("Item não encontrado");

            // Preenche o modal
            const modal = document.getElementById("modal");
            modal.innerHTML = `
                <div class="modal-content">
                    <span class="close" onclick="closeModal()">&times;</span>
                    <h2>${item.nome}</h2>
                    <p>Score: ${item.score}</p>
                    <p>Data: ${item.data}</p>
                    <p>Sugestões: ${item.sugestoes || '-'}</p>
                    <div class="medalha">
                        ${item.score >= 80 ? "🥇" : item.score >= 50 ? "🥈" : "🥉"}
                    </div>
                </div>
            `;
            modal.style.display = "block";
        });
}

function closeModal() {
    const modal = document.getElementById("modal");
    modal.style.display = "none";
}


async function sendMessage() {
    const input = document.getElementById("chatInput");
    const chat = document.getElementById("chatMessages");

    const userText = input.value.trim();
    if (!userText) return;

    // 1️⃣ Mostra mensagem do usuário IMEDIATAMENTE
    appendMessage("user", userText);
    input.value = "";

    // 2️⃣ Mostra indicador digitando
    const typingId = appendTypingIndicator();

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ msg: userText })
        });

        const data = await response.json();

        // Remove indicador
        removeTypingIndicator(typingId);

        // 3️⃣ Digitação rápida simulada
        typeMessage("bot", data.response);

    } catch (err) {
        removeTypingIndicator(typingId);
        appendMessage("bot", "Erro ao processar.");
    }
}

function appendMessage(role, text) {
    const chat = document.getElementById("chatMessages");

    const message = document.createElement("div");
    message.className = `message ${role}`;

    message.innerHTML = `
        <div class="avatar">
            <i class="fas ${role === "user" ? "fa-user" : "fa-robot"}"></i>
        </div>
        <div class="text">${marked.parse(text)}</div>
    `;

    chat.appendChild(message);
    scrollToBottom();
}

function appendTypingIndicator() {
    const chat = document.getElementById("chatMessages");

    const id = "typing-" + Date.now();

    const message = document.createElement("div");
    message.className = "message bot";
    message.id = id;

    message.innerHTML = `
        <div class="avatar"><i class="fas fa-robot"></i></div>
        <div class="text typing">
            <span></span><span></span><span></span>
        </div>
    `;

    chat.appendChild(message);
    scrollToBottom();

    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function typeMessage(role, text) {
    const chat = document.getElementById("chatMessages");

    const message = document.createElement("div");
    message.className = `message ${role}`;

    message.innerHTML = `
        <div class="avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="text"></div>
    `;

    chat.appendChild(message);

    const textContainer = message.querySelector(".text");

    let i = 0;
    const speed = 5; // 🔥 menor = mais rápido

    function type() {
        if (i < text.length) {
            textContainer.innerHTML = marked.parse(text.slice(0, i));
            i++;
            scrollToBottom();
            setTimeout(type, speed);
        }
    }

    type();
}

// Loading helpers
function showLoading(message) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'flex';
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

function addMessage(sender, text) {
    const chatMessages = document.getElementById('chatMessages');
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender);

    // Se for o bot, processa o Markdown. Se for usuário, apenas texto.
    const content = sender === 'bot' ? marked.parse(text) : text;

    msgDiv.innerHTML = `
        <div class="avatar"><i class="fas fa-${sender === 'bot' ? 'robot' : 'user'}"></i></div>
        <div class="text">${content}</div>
    `;

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    hideLoading(); // 🔥 blindagem contra overlay preso
    loadHistorico();
});

window.onload = () => {
    // App is initialized
};