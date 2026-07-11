/* ── State ─────────────────────────────────────────────────────────────── */
const state = {
    sessionId: null,
    pendingOptions: null,
};

/* ── DOM refs ──────────────────────────────────────────────────────────── */
const $ = (sel) => document.querySelector(sel);
const chatLog =       document.getElementById('chat-log');
const sceneLocation = document.getElementById('scene-location');
const sceneTags =     document.getElementById('scene-tags');
const optionsPanel =  document.getElementById('options-panel');
const inputSpeech =   document.getElementById('input-speech');
const inputAction =   document.getElementById('input-action');
const sendBtn =       document.getElementById('send-btn');
const newSessionBtn = document.getElementById('new-session-btn');
const spinner =       document.getElementById('spinner');
const emptyState =    document.getElementById('empty-state');

/* ── Helpers ──────────────────────────────────────────────────────────── */
function setLoading(on) {
    const disable = on || !state.sessionId;
    inputSpeech.disabled = disable;
    inputAction.disabled = disable;
    sendBtn.disabled = disable;
    spinner.classList.toggle('active', on);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function scrollToBottom() {
    chatLog.scrollTop = chatLog.scrollHeight;
}

/* ── Render scene ──────────────────────────────────────────────────────── */
function renderScene(scene, changedKeys = []) {
    if (!scene) return;

    sceneLocation.textContent = `${scene.location} — ${scene.time_of_day}`;

    sceneTags.innerHTML = '';
    for (const [key, val] of Object.entries(scene.physical_facts || {})) {
        const tag = document.createElement('span');
        tag.className = 'scene-tag';
        if (changedKeys.includes(key)) tag.classList.add('flash');
        tag.textContent = `${key}: ${val}`;
        sceneTags.appendChild(tag);
    }
}

/* ── Render message ────────────────────────────────────────────────────── */
const SPEAKER_ICONS = {
    'Narrator': '🎭',
    'Player':   '⚔️',
    'C1':       '⚔️',
    'C2':       '🔮',
};

const SPEAKER_LABELS = {
    'Narrator': 'Narrator',
    'Player':   'Você (Thorn)',
    'C1':       'Thorn',
    'C2':       'Lyra',
};

function addMessage(speaker, content, contentType) {
    // Se é "speech" do Player e o Player controla C1, mapeia pra Player
    const displaySpeaker = (speaker === 'C1' && contentType === 'speech') ? 'Player' : speaker;

    const msgClass = displaySpeaker === 'Player' ? 'msg-player'
                   : displaySpeaker === 'Narrator' ? 'msg-narrator'
                   : 'msg-npc';

    const icon = SPEAKER_ICONS[displaySpeaker] || '💬';
    const label = SPEAKER_LABELS[displaySpeaker] || displaySpeaker;

    const msg = document.createElement('div');
    msg.className = `msg ${msgClass}`;

    const header = document.createElement('div');
    header.className = 'msg-header';
    header.textContent = `${icon} ${label}`;
    msg.appendChild(header);

    const body = document.createElement('div');
    body.className = 'msg-content';

    // Renderiza **texto** como pensamento (itálico)
    const parts = content.split(/(\*\*[^*]+\*\*)/g);
    for (const part of parts) {
        if (part.startsWith('**') && part.endsWith('**')) {
            const span = document.createElement('span');
            span.className = 'thought';
            span.textContent = part.slice(2, -2);
            body.appendChild(span);
        } else {
            body.appendChild(document.createTextNode(part));
        }
    }

    msg.appendChild(body);
    chatLog.appendChild(msg);

    // Tira empty state se for a primeira mensagem
    emptyState.style.display = 'none';
    scrollToBottom();
}

/* ── Player Options ────────────────────────────────────────────────────── */
function renderOptions(options) {
    optionsPanel.innerHTML = '';
    if (!options || options.length === 0) {
        optionsPanel.classList.remove('active');
        state.pendingOptions = null;
        return;
    }

    optionsPanel.classList.add('active');
    state.pendingOptions = options;

    for (const opt of options) {
        const btn = document.createElement('button');
        btn.className = 'option-btn';

        const label = document.createElement('span');
        label.className = 'opt-label';
        label.textContent = `${opt.index + 1}. ${opt.label}`;
        btn.appendChild(label);

        if (opt.description) {
            const desc = document.createElement('span');
            desc.className = 'opt-desc';
            desc.textContent = opt.description;
            btn.appendChild(desc);
        }

        btn.addEventListener('click', () => {
            // Preenche action com o label e envia automaticamente
            inputAction.value = opt.label;
            sendTurn(opt.index);
        });

        optionsPanel.appendChild(btn);
    }
}

/* ── API Calls ─────────────────────────────────────────────────────────── */
async function startSession() {
    setLoading(true);

    try {
        const res = await fetch('/session/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}),
        });
        const data = await res.json();

        if (data.session_id) {
            state.sessionId = data.session_id;

            // Renderiza cena direto do state que veio na resposta
            if (data.state && data.state.scene) {
                renderScene(data.state.scene);
            }

            // Habilita inputs
            inputSpeech.disabled = false;
            inputAction.disabled = false;
            sendBtn.disabled = false;
            inputSpeech.focus();

            console.log(`Sessão iniciada: ${state.sessionId}`);
        }
    } catch (err) {
        console.error('Erro ao iniciar sessão:', err);
        alert('Erro ao conectar ao servidor. Verifique se o backend está rodando.');
    } finally {
        setLoading(false);
    }
}

async function sendTurn(chosenOption = null) {
    const speech = inputSpeech.value.trim();
    const action = inputAction.value.trim();

    // Se chosenOption foi fornecido (clique num botão), usa ele
    const chosenOptionVal = chosenOption !== null ? chosenOption : undefined;

    setLoading(true);
    renderOptions(null); // esconde options enquanto processa

    try {
        const res = await fetch(`/session/${state.sessionId}/turn`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                speech: speech || '',
                action: action || '',
                chosen_option: chosenOptionVal,
            }),
        });
        const data = await res.json();

        // Se recebeu {type: "options", options: [...]} — mostra opções, não avança
        if (data.type === 'options') {
            renderOptions(data.options);
            inputSpeech.value = '';
            inputAction.value = '';
            inputSpeech.focus();
            setLoading(false);
            return;
        }

        // Narração
        if (data.narration) {
            addMessage('Narrator', data.narration, 'narration');
        }

        // Resposta do personagem
        if (data.character_response) {
            const speaker = data.next_speaker || 'C2';
            addMessage(speaker, data.character_response, 'speech');
        }

        // Atualiza cena
        if (data.scene_update) {
            const stateRes = await fetch(`/session/${state.sessionId}/state`);
            const gameState = await stateRes.json();
            const changedKeys = Object.keys(data.scene_update);
            renderScene(gameState.scene, changedKeys);
        }

        // Player options (se veio junto com a resposta normal)
        if (data.player_options && data.player_options.length > 0) {
            renderOptions(data.player_options);
        } else {
            renderOptions(null);
        }

        // Limpa inputs
        inputSpeech.value = '';
        inputAction.value = '';
        inputSpeech.focus();

    } catch (err) {
        console.error('Erro ao enviar turno:', err);
    } finally {
        setLoading(false);
    }
}

/* ── Event Listeners ───────────────────────────────────────────────────── */
sendBtn.addEventListener('click', () => sendTurn());

inputAction.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendTurn();
    }
});

inputSpeech.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        inputAction.focus();
    }
});

newSessionBtn.addEventListener('click', () => {
    // Limpa tudo
    chatLog.innerHTML = '';
    optionsPanel.innerHTML = '';
    optionsPanel.classList.remove('active');
    renderOptions(null);
    inputSpeech.value = '';
    inputAction.value = '';
    state.sessionId = null;
    state.pendingOptions = null;
    emptyState.style.display = 'flex';
    sceneLocation.textContent = '';
    sceneTags.innerHTML = '';

    startSession();
});

/* ── Init ──────────────────────────────────────────────────────────────── */
startSession();
