const CATALOG_ENDPOINT = '/api/v1/dev/presentation-scenes';
const REVIEW_STORAGE_KEY = 'brafoot.presentationSceneReviews.v1';

const pitch = document.getElementById('scenePitch');
const playerLayer = document.getElementById('playerLayer');
const ball = document.getElementById('sceneBall');
const catalogElement = document.getElementById('sceneCatalog');
const catalogSummary = document.getElementById('catalogSummary');
const scenarioCategory = document.getElementById('scenarioCategory');
const scenarioTitle = document.getElementById('scenarioTitle');
const sceneCounter = document.getElementById('sceneCounter');
const playbackState = document.getElementById('playbackState');
const narration = document.getElementById('sceneNarration');
const speedControl = document.getElementById('playbackSpeed');
const playButton = document.getElementById('playScenario');
const resetButton = document.getElementById('resetScenario');
const reviewStatus = document.getElementById('reviewStatus');
const reviewNote = document.getElementById('reviewNote');
const saveReviewNoteButton = document.getElementById('saveReviewNote');
const editReviewNoteButton = document.getElementById('editReviewNote');
const reviewSceneCount = document.getElementById('reviewSceneCount');
const approvedSceneCount = document.getElementById('approvedSceneCount');
const exportSceneReviewsButton = document.getElementById('exportSceneReviews');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

let catalog = null;
let activeScenario = null;
let currentAnimations = [];
let runToken = 0;
let reviews = loadReviews();
let activeCatalogView = 'review';

function loadReviews() {
    try {
        return JSON.parse(window.localStorage.getItem(REVIEW_STORAGE_KEY)) || {};
    } catch {
        return {};
    }
}

function reviewKey(scenario) {
    return `${scenario.id}@${scenario.version}`;
}

function currentReview(scenario) {
    const stored = reviews[reviewKey(scenario)] || {};
    return {
        ...stored,
        status: stored.status || scenario.status || 'pending',
        note: stored.note || '',
        draft_note: stored.draft_note ?? stored.note ?? '',
        note_locked: Boolean(stored.note_locked),
    };
}

function persistReviews() {
    window.localStorage.setItem(REVIEW_STORAGE_KEY, JSON.stringify(reviews));
}

function saveReview(status) {
    if (!activeScenario) return;
    saveReviewDraft();
    const existing = currentReview(activeScenario);
    reviews[reviewKey(activeScenario)] = {
        ...existing,
        status,
        reviewed_at: new Date().toISOString(),
    };
    persistReviews();
    activeCatalogView = status === 'approved' ? 'approved' : 'review';
    updateReviewPanel();
    updateCatalogTabs();
    renderCatalog();
}

function saveReviewDraft() {
    if (!activeScenario || reviewNote.readOnly) return;
    const existing = currentReview(activeScenario);
    reviews[reviewKey(activeScenario)] = {
        ...existing,
        draft_note: reviewNote.value,
        updated_at: new Date().toISOString(),
    };
    persistReviews();
    saveReviewNoteButton.disabled = !reviewNote.value.trim();
}

function lockReviewNote() {
    if (!activeScenario || !reviewNote.value.trim()) return;
    const existing = currentReview(activeScenario);
    const note = reviewNote.value.trim();
    reviews[reviewKey(activeScenario)] = {
        ...existing,
        note,
        draft_note: note,
        note_locked: true,
        note_saved_at: new Date().toISOString(),
    };
    persistReviews();
    updateReviewPanel();
}

function unlockReviewNote() {
    if (!activeScenario) return;
    const existing = currentReview(activeScenario);
    reviews[reviewKey(activeScenario)] = {
        ...existing,
        draft_note: existing.note,
        note_locked: false,
        updated_at: new Date().toISOString(),
    };
    persistReviews();
    updateReviewPanel();
    reviewNote.focus();
}

function statusLabel(status) {
    if (status === 'approved') return 'Aprovada';
    if (status === 'changes_requested') return 'Precisa de ajustes';
    if (status === 'ready_for_review') return 'Pronta para nova revisão';
    return 'Pendente';
}

function exportSceneReviews() {
    if (!catalog) return;
    const exportedReviews = catalog.scenarios
        .map((scenario) => ({
            scenario_id: scenario.id,
            scenario_title: scenario.title,
            scenario_version: scenario.version,
            ...currentReview(scenario),
        }))
        .filter((review) => (
            review.status !== 'pending'
            || review.note
            || review.draft_note
        ));
    const payload = {
        catalog_version: catalog.catalog_version,
        exported_at: new Date().toISOString(),
        reviews: exportedReviews,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
        type: 'application/json',
    });
    const downloadUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `brafoot-revisoes-cenas-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(downloadUrl);
}

function updateReviewPanel() {
    if (!activeScenario) return;
    const review = currentReview(activeScenario);
    reviewStatus.textContent = statusLabel(review.status);
    reviewStatus.className = `review-status ${review.status}`;
    reviewNote.value = review.note_locked ? review.note : review.draft_note;
    reviewNote.readOnly = review.note_locked;
    saveReviewNoteButton.hidden = review.note_locked;
    saveReviewNoteButton.disabled = !reviewNote.value.trim();
    editReviewNoteButton.hidden = !review.note_locked;
}

function visibleScenarios() {
    if (!catalog) return [];
    return catalog.scenarios.filter((scenario) => {
        const approved = currentReview(scenario).status === 'approved';
        return activeCatalogView === 'approved' ? approved : !approved;
    });
}

function updateCatalogTabs() {
    if (!catalog) return;
    const approvedCount = catalog.scenarios.filter(
        (scenario) => currentReview(scenario).status === 'approved',
    ).length;
    reviewSceneCount.textContent = catalog.scenarios.length - approvedCount;
    approvedSceneCount.textContent = approvedCount;
    document.querySelectorAll('[data-catalog-view]').forEach((button) => {
        const active = button.dataset.catalogView === activeCatalogView;
        button.classList.toggle('active', active);
        button.setAttribute('aria-selected', String(active));
    });
}

function setCatalogView(view) {
    activeCatalogView = view;
    updateCatalogTabs();
    renderCatalog();
    const visible = visibleScenarios();
    if (visible.length && !visible.some((scenario) => scenario.id === activeScenario?.id)) {
        selectScenario(visible[0]);
    }
}

function renderCatalog() {
    if (!catalog) return;
    catalogElement.replaceChildren();
    updateCatalogTabs();
    const visible = visibleScenarios();
    catalog.groups.forEach((group) => {
        const scenarios = visible.filter((scenario) => scenario.category === group.id);
        if (!scenarios.length) return;
        const section = document.createElement('section');
        section.className = 'catalog-group';
        const heading = document.createElement('h3');
        heading.textContent = group.title;
        section.appendChild(heading);

        scenarios.forEach((scenario) => {
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'scenario-card';
                button.dataset.scenarioId = scenario.id;
                button.dataset.review = currentReview(scenario).status;
                if (scenario.id === activeScenario?.id) button.classList.add('active');

                const title = document.createElement('strong');
                title.textContent = scenario.title;
                const description = document.createElement('small');
                description.textContent = scenario.description;
                button.append(title, description);
                button.addEventListener('click', () => selectScenario(scenario));
                section.appendChild(button);
            });
        catalogElement.appendChild(section);
    });
    if (!visible.length) {
        const empty = document.createElement('p');
        empty.className = 'catalog-empty';
        empty.textContent = activeCatalogView === 'approved'
            ? 'Nenhuma cena foi aprovada ainda.'
            : 'Todas as cenas atuais estão aprovadas.';
        catalogElement.appendChild(empty);
    }
}

function playerElement(side, playerId) {
    return playerLayer.querySelector(
        `.match-player[data-team="${side}"][data-player-id="${playerId}"]`,
    );
}

function renderPlayers(players) {
    playerLayer.replaceChildren();
    players.forEach((player) => {
        const element = document.createElement('span');
        element.className = `match-player ${player.side}`;
        element.dataset.team = player.side;
        element.dataset.playerId = player.player_id;
        element.style.setProperty('--x', player.x);
        element.style.setProperty('--y', player.y);
        element.setAttribute('aria-label', `Jogador ${player.player_id} ${player.side}`);

        const marker = document.createElement('span');
        marker.className = 'player-marker';
        marker.textContent = player.player_id;
        element.appendChild(marker);
        playerLayer.appendChild(element);
    });
}

function positionBall(point) {
    ball.style.left = `${point.x}%`;
    ball.style.top = `${point.y}%`;
}

function positionPlayer(side, playerId, point) {
    const player = playerElement(side, playerId);
    if (!player) return;
    player.style.setProperty('--x', point.x);
    player.style.setProperty('--y', point.y);
}

function resetScenario() {
    if (!activeScenario) return;
    runToken += 1;
    cancelAnimations();
    renderPlayers(activeScenario.initial_state.players);
    positionBall(activeScenario.initial_state.ball_position);
    ball.hidden = !activeScenario.ball_visible;
    sceneCounter.textContent = `0 / ${activeScenario.scenes.length}`;
    playbackState.textContent = 'Cenário reiniciado';
    narration.textContent = activeScenario.description;
    playButton.disabled = false;
    resetButton.disabled = false;
}

function cancelAnimations() {
    currentAnimations.forEach((animation) => animation.cancel());
    currentAnimations = [];
}

function animationFrames(keyframes, durationMs) {
    return keyframes.map((keyframe) => ({
        left: `${keyframe.x}%`,
        top: `${keyframe.y}%`,
        offset: keyframe.at_ms / durationMs,
    }));
}

async function animateScene(scene, scenario, token) {
    const speed = Number(speedControl.value);
    const duration = reducedMotion.matches ? 0 : scene.duration_ms / speed;
    const ballEnd = scene.keyframes.at(-1);
    const tracks = scene.player_tracks || [];

    narration.textContent = scene.narration;
    playbackState.textContent = scene.event_type === 'movement'
        ? 'Movimento sem bola'
        : scene.event_type.replaceAll('_', ' ');

    if (!duration || typeof ball.animate !== 'function') {
        if (scenario.ball_visible) positionBall(ballEnd);
        tracks.forEach((track) => {
            positionPlayer(track.side, track.player_id, track.keyframes.at(-1));
        });
        return;
    }

    const animations = [];
    if (scenario.ball_visible) {
        animations.push(ball.animate(animationFrames(scene.keyframes, scene.duration_ms), {
            duration,
            easing: 'linear',
            fill: 'forwards',
        }));
    }
    tracks.forEach((track) => {
        const player = playerElement(track.side, track.player_id);
        if (!player) return;
        animations.push(player.animate(animationFrames(track.keyframes, scene.duration_ms), {
            duration,
            easing: 'linear',
            fill: 'forwards',
        }));
    });
    currentAnimations = animations;
    await Promise.all(animations.map((animation) => animation.finished.catch(() => {})));
    if (token !== runToken) return;

    cancelAnimations();
    if (scenario.ball_visible) positionBall(ballEnd);
    tracks.forEach((track) => {
        positionPlayer(track.side, track.player_id, track.keyframes.at(-1));
    });
}

async function playScenario() {
    if (!activeScenario) return;
    resetScenario();
    const token = runToken;
    playButton.disabled = true;
    for (const [index, scene] of activeScenario.scenes.entries()) {
        if (token !== runToken) return;
        sceneCounter.textContent = `${index + 1} / ${activeScenario.scenes.length}`;
        await animateScene(scene, activeScenario, token);
    }
    if (token !== runToken) return;
    playbackState.textContent = 'Reprodução concluída';
    playButton.disabled = false;
}

function selectScenario(scenario) {
    activeScenario = scenario;
    const group = catalog.groups.find((item) => item.id === scenario.category);
    scenarioCategory.textContent = group?.title || scenario.category;
    scenarioTitle.textContent = scenario.title;
    updateReviewPanel();
    renderCatalog();
    resetScenario();
    window.setTimeout(playScenario, 120);
}

async function loadCatalog() {
    try {
        const response = await fetch(CATALOG_ENDPOINT);
        if (!response.ok) throw new Error(`Catálogo indisponível: ${response.status}`);
        catalog = await response.json();
        catalogSummary.textContent = `${catalog.scenarios.length} cenários · versão ${catalog.catalog_version}`;
        renderCatalog();
        const firstReviewScenario = visibleScenarios()[0];
        if (firstReviewScenario) {
            selectScenario(firstReviewScenario);
        } else {
            setCatalogView('approved');
        }
    } catch (error) {
        playbackState.textContent = 'Falha no catálogo';
        narration.textContent = error.message;
        console.error(error);
    }
}

playButton.addEventListener('click', playScenario);
resetButton.addEventListener('click', resetScenario);
reviewNote.addEventListener('input', saveReviewDraft);
saveReviewNoteButton.addEventListener('click', lockReviewNote);
editReviewNoteButton.addEventListener('click', unlockReviewNote);
exportSceneReviewsButton.addEventListener('click', exportSceneReviews);
document.querySelectorAll('.review-actions [data-review]').forEach((button) => {
    button.addEventListener('click', () => saveReview(button.dataset.review));
});
document.querySelectorAll('[data-catalog-view]').forEach((button) => {
    button.addEventListener('click', () => setCatalogView(button.dataset.catalogView));
});

loadCatalog();
