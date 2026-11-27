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
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

let catalog = null;
let activeScenario = null;
let currentAnimations = [];
let runToken = 0;
let reviews = loadReviews();

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
    return reviews[reviewKey(scenario)] || { status: 'pending', note: '' };
}

function saveReview(status) {
    if (!activeScenario) return;
    reviews[reviewKey(activeScenario)] = {
        status,
        note: reviewNote.value.trim(),
        reviewed_at: new Date().toISOString(),
    };
    window.localStorage.setItem(REVIEW_STORAGE_KEY, JSON.stringify(reviews));
    updateReviewPanel();
    renderCatalog();
}

function statusLabel(status) {
    if (status === 'approved') return 'Aprovada';
    if (status === 'changes_requested') return 'Precisa de ajustes';
    return 'Pendente';
}

function updateReviewPanel() {
    if (!activeScenario) return;
    const review = currentReview(activeScenario);
    reviewStatus.textContent = statusLabel(review.status);
    reviewStatus.className = `review-status ${review.status}`;
    reviewNote.value = review.note;
}

function renderCatalog() {
    if (!catalog) return;
    catalogElement.replaceChildren();
    catalog.groups.forEach((group) => {
        const section = document.createElement('section');
        section.className = 'catalog-group';
        const heading = document.createElement('h3');
        heading.textContent = group.title;
        section.appendChild(heading);

        catalog.scenarios
            .filter((scenario) => scenario.category === group.id)
            .forEach((scenario) => {
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
        selectScenario(catalog.scenarios[0]);
    } catch (error) {
        playbackState.textContent = 'Falha no catálogo';
        narration.textContent = error.message;
        console.error(error);
    }
}

playButton.addEventListener('click', playScenario);
resetButton.addEventListener('click', resetScenario);
document.querySelectorAll('[data-review]').forEach((button) => {
    button.addEventListener('click', () => saveReview(button.dataset.review));
});

loadCatalog();
