// ===============================
// UTILIDADES GERAIS
// ===============================

function scrollToBottom() {
    const chat = document.getElementById("chatMessages");
    if (!chat) return;
    chat.scrollTop = chat.scrollHeight;
}

function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.style.display = 'flex';
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.style.display = 'none';
}


// ===============================
// CHAT
// ===============================

async function sendMessage() {
    const input = document.getElementById("chatInput");
    const chat = document.getElementById("chatMessages");

    if (!input || !chat) return;

    const userText = input.value.trim();
    if (!userText) return;

    appendMessage("user", userText);
    input.value = "";

    const typingId = appendTypingIndicator();

    try {
        const response = await fetch("/chat_orquestrador", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ msg: userText }),
            credentials: "include" // 🔥 ADICIONE
        });

        const data = await response.json();

        removeTypingIndicator(typingId);
        typeMessage("bot", data.response);

    } catch (err) {
        removeTypingIndicator(typingId);
        appendMessage("bot", "Erro ao processar.");
    }
}

function appendMessage(role, text) {
    const chat = document.getElementById("chatMessages");
    if (!chat) return;

    const message = document.createElement("div");
    message.className = `message ${role}`;

    message.innerHTML = `
        <div class="avatar">
            <i class="fas ${role === "user" ? "fa-user" : "fa-robot"}"></i>
        </div>
        <div class="text">${typeof marked !== "undefined" ? marked.parse(text) : text}</div>
    `;

    chat.appendChild(message);
    scrollToBottom();
}

function appendTypingIndicator() {
    const chat = document.getElementById("chatMessages");
    if (!chat) return null;

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
    if (!id) return;
    const el = document.getElementById(id);
    if (el) el.remove();
}

function typeMessage(role, text) {
    const chat = document.getElementById("chatMessages");
    if (!chat) return;

    const message = document.createElement("div");
    message.className = `message ${role}`;

    message.innerHTML = `
        <div class="avatar"><i class="fas fa-robot"></i></div>
        <div class="text"></div>
    `;

    chat.appendChild(message);

    const textContainer = message.querySelector(".text");

    let i = 0;
    const speed = 5;

    function type() {
        if (i <= text.length) {
            const slice = text.slice(0, i);
            textContainer.innerHTML =
                typeof marked !== "undefined" ? marked.parse(slice) : slice;
            i++;
            scrollToBottom();
            setTimeout(type, speed);
        }
    }

    type();
}


// ===============================
// UPLOAD + RELATÓRIO
// ===============================

async function uploadNoChat() {
    const fileInput = document.getElementById('fileInput');
    const chat = document.getElementById("chatMessages");

    if (!fileInput || !chat) return;

    const file = fileInput.files[0];
    if (!file) {
        alert("Selecione um PDF.");
        return;
    }

    appendMessage("user", "📄 Enviou um currículo...");
    showLoading();

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/upload_curriculo", {
            method: "POST",
            body: formData,
            credentials: "include" // 🔥 ADICIONE
        });

        const data = await response.json();
        renderRelatorio(data.info);

    } catch (err) {
        appendMessage("bot", "Erro ao analisar currículo.");
    } finally {
        hideLoading();
    }
}

function renderRelatorio(data) {
    const chat = document.getElementById("chatMessages");
    if (!chat) return;

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
    scrollToBottom();
}


// ===============================
// HISTÓRICO
// ===============================

async function loadHistorico() {
    const list = document.getElementById('historicoList');
    if (!list) return; // 🔥 blindagem

    try {
        const response = await fetch('/historico', {
            credentials: "include"
        });
        const data = await response.json();

        // renderiza todos os itens do histórico
        list.innerHTML = data.map(item => `
            <div class="historico-item" onclick="showModal('${item.id}')">
                <p><strong>${item.nome}</strong></p>
                <p>Score: ${item.score}</p>
                <p>${item.data}</p>
            </div>
        `).join('');

    } catch (err) {
        console.error("Erro ao carregar histórico:", err);
        list.innerHTML = "<p>Não foi possível carregar o histórico.</p>";
    }
}


// ===============================
// DASHBOARD
// ===============================

let scoreChartInstance = null;

async function loadDashboard() {
    const totalEl = document.getElementById('totalAnalises');
    const avgEl = document.getElementById('scoreMedio');
    const canvas = document.getElementById('scoreChart');

    if (!totalEl || !avgEl || !canvas) return;

    const response = await fetch('/historico');
    const data = await response.json();

    const total = data.length;
    const scores = data.map(item => item.score);
    const avg = scores.length ?
        (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(2) :
        0;

    totalEl.textContent = total;
    avgEl.textContent = avg;

    if (scoreChartInstance) {
        scoreChartInstance.destroy();
    }

    scoreChartInstance = new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels: data.map((_, i) => `Análise ${i + 1}`),
            datasets: [{
                label: 'Score',
                data: scores
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true, max: 100 }
            },
            onClick: (evt, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const item = data[index];
                    showModal(item.id); // abre o modal com o histórico
                }
            }
        }
    });
}


// ===============================
// INICIALIZAÇÃO SEGURA
// ===============================

document.addEventListener('DOMContentLoaded', () => {
    hideLoading();
    loadHistorico(); // Só roda se existir elemento
});