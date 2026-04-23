// ── LÊ O team_id DA URL /clube/1 ──
const pathParts = window.location.pathname.split('/');
const TEAM_ID = parseInt(pathParts[pathParts.length - 1]) || 1;
const BASE_URL = '';

// Ordem de exibição no campo (ataque → goleiro)
const ORDEM_CAMPO = ['ATA', 'MEI', 'VOL', 'LAT', 'ZAG', 'GOL'];

// Posições X no campo por posição e índice dentro da linha
const POSICOES_CAMPO = {
    GOL: [[50, 88]],
    ZAG: [[33, 74], [67, 74]],
    LAT: [[12, 68], [88, 68]],
    VOL: [[35, 55], [65, 55]],
    MEI: [[20, 38], [50, 38], [80, 38]],
    ATA: [[20, 20], [50, 14], [80, 20]],
};

let todosJogadores = [];
let titularesAtivos = [];
let draggedReserva = null;

// ── TOAST ──
function showToast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2500);
}

// ── MONTA TITULARES AUTOMATICAMENTE ──
function montarTitulares(jogadores) {
    const LIMITES = { GOL: 1, ZAG: 2, LAT: 2, VOL: 2, MEI: 1, ATA: 3 };
    const porPos = {};
    jogadores.forEach(j => {
        if (!porPos[j.posicao]) porPos[j.posicao] = [];
        porPos[j.posicao].push(j);
    });

    const titulares = [];
    let total = 0;

    ORDEM_CAMPO.forEach(pos => {
        const lista = porPos[pos] || [];
        const limite = LIMITES[pos] || 2;
        const coords = POSICOES_CAMPO[pos] || [];
        lista.forEach((j, i) => {
            if (i < limite && total < 11) {
                const [x, y] = coords[i] || [50, 50];
                titulares.push({ nome: j.nome, numero: j.number, posicao: j.posicao, x, y });
                total++;
            }
        });
    });

    return titulares;
}

// ── RENDER CAMPO ──
function renderCampo() {
    const campo = document.getElementById('campo');
    campo.querySelectorAll('.jogador-campo').forEach(el => el.remove());

    titularesAtivos.forEach((t, idx) => {
        const el = document.createElement('div');
        el.className = 'jogador-campo';
        el.style.left = t.x + '%';
        el.style.top = t.y + '%';
        el.dataset.idx = idx;
        el.innerHTML = `
      <div class="bolinha">${t.numero}</div>
      <div class="nome-campo">${t.nome.split(' ')[0]}</div>
      <div class="pos-badge">${t.posicao}</div>
    `;

        el.addEventListener('dragover', e => { e.preventDefault(); el.classList.add('drag-over-target'); });
        el.addEventListener('dragleave', () => el.classList.remove('drag-over-target'));
        el.addEventListener('drop', e => {
            e.preventDefault();
            el.classList.remove('drag-over-target');
            if (draggedReserva) fazerSubstituicao(idx, draggedReserva);
        });

        campo.appendChild(el);
    });
}

// ── RENDER RESERVAS ──
function renderReservas(reservas) {
    const lista = document.getElementById('reservasLista');
    if (!reservas.length) {
        lista.innerHTML = '<div style="color:rgba(255,255,255,0.2);font-size:0.75rem;padding:12px;">Nenhum reserva disponível.</div>';
        return;
    }

    lista.innerHTML = '';
    reservas.forEach(j => {
        const card = document.createElement('div');
        card.className = 'reserva-card';
        card.draggable = true;
        card.innerHTML = `
      <div class="reserva-num">${j.number}</div>
      <div class="reserva-info">
        <div class="reserva-nome">${j.nome}</div>
        <div class="reserva-pos">${j.posicao}</div>
      </div>
      <div class="reserva-drag-hint">↕ arrastar</div>
    `;

        card.addEventListener('dragstart', () => {
            draggedReserva = { nome: j.nome, numero: j.number, posicao: j.posicao };
            card.classList.add('dragging');
            document.getElementById('campo').classList.add('drag-active');
        });
        card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
            document.getElementById('campo').classList.remove('drag-active');
            draggedReserva = null;
        });

        lista.appendChild(card);
    });
}

// ── SUBSTITUIÇÃO ──
function fazerSubstituicao(idxTitular, reserva) {
    const anterior = { ...titularesAtivos[idxTitular] };
    titularesAtivos[idxTitular] = {
        nome: reserva.nome, numero: reserva.numero,
        posicao: reserva.posicao, x: anterior.x, y: anterior.y
    };

    const nomesT = titularesAtivos.map(t => t.nome);
    const reservas = todosJogadores.filter(j => !nomesT.includes(j.nome));

    renderCampo();
    renderReservas(reservas);
    showToast(`✦ ${anterior.nome} → ${reserva.nome}`);
}

// ── GERAR DESCRIÇÃO VIA CLAUDE API ──
async function gerarDescricaoCraque(nomeJogador, nomeTime) {
    const descEl = document.getElementById('craqueDesc');
    descEl.textContent = 'Gerando análise...';
    descEl.classList.add('loading');

    try {
        const response = await fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: 'claude-sonnet-4-20250514',
                max_tokens: 1000,
                messages: [{
                    role: 'user',
                    content: `Escreva exatamente 2 frases curtas e diretas sobre por que ${nomeJogador} é o craque do ${nomeTime} no Brasileirão 2026. Foque em qualidades técnicas, liderança e impacto no jogo. Tom jornalístico, sem exageros. Responda apenas as 2 frases, sem introdução.`
                }]
            })
        });

        const data = await response.json();
        const texto = data.content?.[0]?.text || 'Análise indisponível.';
        descEl.textContent = texto;
        descEl.classList.remove('loading');
    } catch (e) {
        descEl.textContent = 'Não foi possível gerar a análise no momento.';
        descEl.classList.remove('loading');
    }
}

// ── INIT ──
async function init() {
    try {
        const [timesRes, jogadoresRes] = await Promise.all([
            fetch(`${BASE_URL}/times/`),
            fetch(`${BASE_URL}/jogadores/`)
        ]);

        const times = await timesRes.json();
        const jogadores = await jogadoresRes.json();

        const time = times.find(t => t.id === TEAM_ID);
        if (!time) throw new Error(`Time id=${TEAM_ID} não encontrado`);

        todosJogadores = jogadores.filter(j => j.team_id === TEAM_ID);

        // ── Preenche header ──
        document.getElementById('nomeTime').textContent = time.nome.toUpperCase();
        document.getElementById('nav-clube').textContent = time.nome;
        document.getElementById('formacao-meta').textContent = time.formacao;
        document.getElementById('formacao-badge').textContent = `Formação: ${time.formacao}`;
        document.title = time.nome;

        if (time.escudo)
            document.getElementById('escudo').src = `/${time.escudo}`;

        if (time.foto_craque)
            document.getElementById('craqueFoto').src = `/${time.foto_craque}`;

        // ── Monta campo ──
        titularesAtivos = montarTitulares(todosJogadores);
        renderCampo();

        // ── Reservas ──
        const nomesT = titularesAtivos.map(t => t.nome);
        const reservas = todosJogadores.filter(j => !nomesT.includes(j.nome));
        renderReservas(reservas);

        // ── Craque ──
        const craque = titularesAtivos.find(j => j.posicao === 'ATA') || titularesAtivos[0];
        if (craque) {
            document.getElementById('craqueNome').textContent = craque.nome.toUpperCase();
            document.getElementById('craquePos').textContent = craque.posicao;
            gerarDescricaoCraque(craque.nome, time.nome);
        }

    } catch (err) {
        console.error('Erro:', err);
        document.getElementById('nomeTime').textContent = 'Erro ao carregar';
    } finally {
        document.getElementById('loadingOverlay').classList.add('hidden');
    }
}

init();