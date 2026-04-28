// ── LÊ O team_id DA URL /clube/1 ──
const pathParts = window.location.pathname.split('/');
const TEAM_ID = parseInt(pathParts[pathParts.length - 1]) || 1;
const BASE_URL = '';

// Ordem de exibição no campo (ataque → goleiro)
const ORDEM_TITULARES = ['GOL', 'ZAG', 'LAT', 'VOL', 'MEI', 'ATA'];
const ORDEM_CAMPO     = ['ATA', 'MEI', 'VOL', 'LAT', 'ZAG', 'GOL'];

const FORMACOES = {
    '4-1-2-1-2': [
    [50, 88],
    [33, 74], [67, 74],
    [12, 70], [88, 70],
    [50, 60],
    [33, 50], [67, 50],
    [50, 40],
    [30, 22], [70, 22],
    ],
    '4-4-2': [
    [50, 88],
    [33, 74], [67, 74],
    [12, 70], [88, 70],
    [20, 52], [40, 52], [60, 52], [80, 52],
    [33, 22], [67, 22],
    ],
    '4-3-3': [
    [50, 88],
    [33, 74], [67, 74],
    [12, 70], [88, 70],
    [25, 55], [50, 50], [75, 55],
    [20, 22], [50, 16], [80, 22],
    ],
    '3-4-3': [
    [50, 88],
    [25, 74], [50, 76], [75, 74],
    [12, 57], [88, 57],
    [33, 52], [67, 52],
    [20, 22], [50, 16], [80, 22],
    ],
    '4-2-3-1': [
    [50, 88],
    [33, 74], [67, 74],
    [12, 70], [88, 70],
    [33, 57], [67, 57],
    [20, 40], [50, 38], [80, 40],
    [50, 20],
    ],
    '3-5-2': [
    [50, 88],
    [25, 74], [50, 76], [75, 74],
    [12, 57], [88, 57],
    [33, 52], [50, 45], [67, 52],
    [33, 22], [67, 22],
    ],
};

const CRAQUES = {
    1:  { nome: "Yuri Alberto",    posicao: "Atacante",    desc: "Yuri Alberto é um centroavante conhecido pela grande mobilidade e disposição física para pressionar a saída de bola adversária. O jogador destaca-se por atacar os espaços em velocidade, sendo uma peça constante nas transições ofensivas do Corinthians." },
    2:  { nome: "Hulk",            posicao: "Atacante",    desc: "Hulk é reconhecido por sua força física excepcional e pelo potente chute de perna esquerda, que o torna uma ameaça constante de longa distância. O atacante é o principal líder técnico do Atlético Mineiro, combinando um faro de gol apurado com uma grande capacidade de servir seus companheiros." },
    3:  { nome: "Kevin Viveros",      posicao: "Atacante",    desc: "Kevin Viveros é um centroavante que se destaca pela explosão física e pela capacidade de ganhar duelos individuais contra os defensores. O atacante colombiano utiliza sua velocidade para explorar a profundidade e finalizar com potência, sendo uma opção de força no setor ofensivo do Furacão." },
    4:  { nome: "Jean Lucas",        posicao: "Volante",    desc: "Jean Lucas é um meio-campista dinâmico, reconhecido pela excelente qualidade técnica no passe e pela capacidade de conduzir a bola entre as linhas adversárias. Com passagens por grandes clubes europeus e convocações para a Seleção Brasileira de base, ele traz uma visão de jogo refinada que o torna um dos pilares criativos do Bahia." },
    5:  { nome: "Danilo",           posicao: "Volante",        desc: "Danilo Barbosa é um meio-campista de grande imposição física e técnica, destacando-se tanto na proteção à defesa quanto na chegada surpresa à área adversária. Sua consistência tática no Botafogo e a capacidade de ditar o ritmo do jogo o transformaram em um dos principais nomes da posição, justificando suas recentes convocações para a Seleção Brasileira." },
    6:  { nome: "Isidro Pitta",   posicao: "Atacante",    desc: "Isidro Pitta é um centroavante de muita entrega física, conhecido por sua capacidade de lutar entre os zagueiros e proteger a posse de bola no pivô. O atacante paraguaio destaca-se pelo excelente posicionamento na área e pelo faro de gol, sendo uma referência fundamental para o esquema ofensivo da equipe." },
    7:  { nome: "Jean Carlos",          posicao: "Meia",    desc: "Jean Carlos é um meio-campista clássico, reconhecido pela sua precisão em cobranças de falta e pela qualidade técnica nos passes de longa distância. O jogador atua como o principal articulador da equipe, utilizando sua visão de jogo para criar chances claras de gol e organizar o setor ofensivo." },
    8:  { nome: "Breno Lopes",          posicao: "Atacante",    desc: "Breno Lopes é um atacante de lado de campo que se destaca pela velocidade e pela capacidade de recomposição tática para ajudar o sistema defensivo. O jogador utiliza sua explosão física para atacar os espaços em profundidade, sendo uma peça importante para as transições rápidas e finalizações em velocidade do Coritiba." },
    9:  { nome: "Kaio Jorge",         posicao: "Atacante",    desc: "Kaio Jorge é um atacante de muita movimentação que se destaca pela inteligência tática ao sair da área para participar da construção das jogadas. O jogador combina boa técnica e capacidade de finalização, sendo uma peça importante para dar dinâmica e profundidade ao setor ofensivo do Cruzeiro." },
    10: { nome: "Arrascaeta",         posicao: "Meia",    desc: "Arrascaeta é um meia de rara inteligência e técnica, considerado um dos maiores criadores de jogadas do futebol sul-americano devido à sua visão de jogo e passes decisivos. O uruguaio combina elegância na condução de bola com uma finalização precisa, sendo o principal responsável por ditar o ritmo criativo do ataque do Flamengo." },
    11: { nome: "Luciano Acosta",     posicao: "Ponta",    desc: "Luciano Acosta é um ponta de baixa estatura que se destaca pela agilidade extrema e pelo controle de bola refinado em espaços curtos. O jogador utiliza sua visão de jogo e drible desconcertante para quebrar linhas defensivas, sendo uma peça fundamental na criação de jogadas ofensivas do Fluminense." },
    12: { nome: "Carlos Vinícius",         posicao: "Atacante",    desc: "Carlos Vinícius é um centroavante de grande porte físico, destacando-se pela força no jogo aéreo e pela eficiência em finalizar jogadas dentro da área. O atacante utiliza sua presença de área para servir como referência ofensiva, sendo uma peça importante para o Grêmio na disputa por bolas longas e no pivô." },
    13: { nome: "Alan Patrick",          posicao: "Meia",    desc: "Alan Patrick é o grande maestro do Internacional, unindo uma visão de jogo extraordinária a uma técnica refinada que dita o ritmo de todo o time. Sua liderança técnica e gols decisivos em momentos cruciais consolidaram sua posição como um dos grandes ídolos recentes da história colorada." },
    14: { nome: "Reinaldo",     posicao: "Lateral/Ala",    desc: "Reinaldo é um lateral de extrema importância ofensiva, sendo uma das principais armas do Mirassol devido aos seus cruzamentos precisos e passes que rompem linhas. Sua participação direta em gols é constante, seja através de assistências ou em cobranças de bola parada que frequentemente decidem partidas para o clube." },
    15: { nome: "John Arias",         posicao: "Meia",        desc: "Jhon Arias é um ponta de alta intensidade que se destaca pelo drible curto e pela capacidade de decidir jogos tanto com assistências precisas quanto com gols. Sua inteligência tática e versatilidade fazem dele uma peça fundamental para o equilíbrio do Palmeiras, sendo uma ameaça constante nas transições ofensivas." },
    16: { nome: "Gabriel Taliari",          posicao: "Atacante",    desc: "Gabriel Taliari é um atacante versátil que se destaca pela boa movimentação técnica e pela facilidade em atuar tanto centralizado quanto pelas beiradas do campo. O jogador possui um faro de gol apurado e grande capacidade de finalização, sendo uma das referências fundamentais para o poder ofensivo do Remo." },
    17: { nome: "Neymar Jr",          posicao: "Meia Atacante",    desc: "Neymar Jr é um atacante de técnica excepcional, reconhecido mundialmente por seu drible imprevisível e pela capacidade criativa de decidir partidas em um único lance. Sua genialidade na condução de bola e precisão nas finalizações fazem dele a maior referência técnica do setor ofensivo e um ícone para a torcida santista." },
    18: { nome: "Calleri",         posicao: "Atacante",        desc: "Calleri é um centroavante de entrega incansável, reconhecido pelo seu faro de gol apurado e pela força física dominante dentro da área adversária. Sua postura aguerrida e identificação profunda com a torcida o tornam o principal líder do elenco, sendo a voz de comando e referência máxima do ataque são-paulino." },
    19: { nome: "Claudio Spinelli",  posicao: "Atacante",    desc: "Claudio Spinelli é um centroavante de boa presença de área que se destaca pela força física e pela capacidade de atuar como pivô para os companheiros. O atacante argentino busca aproveitar sua estatura no jogo aéreo e na finalização de primeira sendo uma referência ofensiva no elenco do Vasco." },
    20: { nome: "Renato Kayzer",      posicao: "Atacante",    desc: "Renato Kayzer é um centroavante de muita entrega física e excelente posicionamento, sendo uma peça fundamental para finalizar as jogadas ofensivas do Vitória. Sua importância é traduzida em gols decisivos e assistências, atuando como o principal homem de referência para garantir a eficiência do ataque rubro-negro." },
};

const TITULARES = {
    1:  [1, 7, 8, 6, 5, 18, 22, 17, 15, 26, 27], // Corinthians
    2:  [34, 42, 39, 38, 43, 55, 59, 51, 50, 65, 68], // Atlético
    3:  [70, 76, 77, 78, 81, 79, 90, 84, 86, 94, 96 ], // Athlético
    4:  [102, 110, 104, 103, 105, 114, 113, 120, 123, 124, 127], // Bahia
    5: [128, 136, 134, 132, 133, 150, 148, 165, 154, 164, 163], // Botafogo
    6: [170, 179, 181, 175, 177, 190, 191, 197, 189, 204, 199], // Bragantino
    7: [211, 218, 220, 214, 229, 240, 230, 236, 231, 250, 246], //Chapecoense
    8: [257, 263, 266, 269, 265, 276, 280, 283, 272, 284, 285], // Coritiba
    9: [288, 297, 290, 293, 291, 301, 305, 308, 302, 303, 316], // Cruzeiro
    10: [321, 328, 327, 326, 330, 337, 336, 344, 350, 349, 341], // Flamengo
    11: [354, 364, 366, 358, 360, 373, 375, 378, 371, 386, 374], // Fluminense
    12: [389, 397, 393, 398, 394, 407, 410, 415, 424, 422, 423], // Gremio
    13: [426, 429, 433, 430, 434, 446, 449, 445, 440, 455, 454], // Internacional
    14: [459, 465, 468, 472, 463, 464, 482, 483, 481, 486, 484], // Mirassol
    15: [492, 496, 499, 498, 502, 512, 511, 508, 507, 506, 518], // Palmeiras
    16: [524, 529, 532, 533, 527, 539, 550, 538, 540, 546, 557], // Remo
    17: [562, 568, 569, 570, 567, 579, 580, 594, 586, 588, 587], //Santos
    18: [600, 606, 608, 605, 613, 623, 618, 617, 628, 630, 629], // São Paulo
    19: [636, 644, 646, 642, 640, 653, 649, 667, 651, 668, 663], // Vasco
    20: [670, 674, 677, 679, 678, 692, 686, 696, 708, 701, 699], // Vitória

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

function montarTitulares(jogadores, POSICOES_CAMPO) {
    const coords = POSICOES_CAMPO;

    return jogadores.map((j, i) => {
        const [x, y] = coords[i] || [50, 50];
        return { id: j.id, nome: j.nome, numero: j.number, posicao: j.posicao, x, y };
    });
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
        <div class="nome-campo">${t.nome}</div>
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
            draggedReserva = { id: j.id, nome: j.nome, numero: j.number, posicao: j.posicao };
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
        id: reserva.id,
        nome: reserva.nome, numero: reserva.numero,
        posicao: reserva.posicao, x: anterior.x, y: anterior.y
};

    const idsT = titularesAtivos.map(t => t.id);
    const reservas = todosJogadores.filter(j => !idsT.includes(j.id));

    renderCampo();
    renderReservas(reservas);
    showToast(`✦ ${anterior.nome} → ${reserva.nome}`);
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
        const POSICOES_CAMPO = FORMACOES[time.formacao] || FORMACOES['4-4-2'];

        if (time.escudo)
            document.getElementById('escudo').src = `${time.escudo}`;

        if (time.foto_craque)
            document.getElementById('craqueFoto').src = `${time.foto_craque}`;

        // ── Monta campo ──
        const idsTitulares = TITULARES[TEAM_ID];
        const jogadoresFiltrados = idsTitulares
            ? idsTitulares.map(id => todosJogadores.find(j => j.id === id)).filter(Boolean)
            : todosJogadores;
        titularesAtivos = montarTitulares(jogadoresFiltrados, POSICOES_CAMPO);
        console.log('filtrados:', jogadoresFiltrados);
        console.log('titulares:', titularesAtivos);

        renderCampo();

        // ── Reservas ──
        const nomesT = titularesAtivos.map(t => t.nome);
        const reservas = todosJogadores.filter(j => !nomesT.includes(j.nome));
        renderReservas(reservas);

        // ── Craque ──
        const craque = CRAQUES[TEAM_ID];
        if (craque) {
            document.getElementById('craqueNome').textContent = craque.nome.toUpperCase();
            document.getElementById('craquePos').textContent = craque.posicao;
            document.getElementById('craqueDesc').textContent = craque.desc;
            document.getElementById('craqueDesc').classList.remove('loading');
        }

    } catch (err) {
        console.error('Erro:', err);
        document.getElementById('nomeTime').textContent = 'Erro ao carregar';
    } finally {
        document.getElementById('loadingOverlay').classList.add('hidden');
    }
}

init();