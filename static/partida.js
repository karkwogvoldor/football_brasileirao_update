const SCENE_ENDPOINT = '/api/v1/presentation/demo-sequence';

const ball = document.getElementById('sceneBall');
const narration = document.getElementById('sceneNarration');
const sceneLabel = document.getElementById('sceneLabel');
const replayButton = document.getElementById('replayScene');
const phase = document.querySelector('.match-phase');
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

let sequenceData = null;
let currentAnimations = [];

function positionBall(keyframe) {
    ball.style.left = `${keyframe.x}%`;
    ball.style.top = `${keyframe.y}%`;
}

function playerElement(side, playerId) {
    return document.querySelector(
        `.match-player[data-team="${side}"][data-player-id="${playerId}"]`,
    );
}

function positionPlayer(side, playerId, keyframe) {
    const player = playerElement(side, playerId);
    if (!player) return;
    player.style.setProperty('--x', keyframe.x);
    player.style.setProperty('--y', keyframe.y);
}

function positionState(state) {
    positionBall(state.ball_position);
    state.players.forEach((player) => {
        positionPlayer(player.side, player.player_id, player);
    });
}

function animationFrames(keyframes, durationMs) {
    return keyframes.map((keyframe) => ({
        left: `${keyframe.x}%`,
        top: `${keyframe.y}%`,
        offset: keyframe.at_ms / durationMs,
    }));
}

function cancelAnimations() {
    currentAnimations.forEach((animation) => animation.cancel());
    currentAnimations = [];
}

async function animateScene(scene) {
    const finalKeyframe = scene.keyframes.at(-1);
    const playerTracks = scene.player_tracks || [];

    if (prefersReducedMotion.matches || typeof ball.animate !== 'function') {
        positionBall(finalKeyframe);
        playerTracks.forEach((track) => {
            positionPlayer(track.side, track.player_id, track.keyframes.at(-1));
        });
        return;
    }

    currentAnimations = [
        ball.animate(animationFrames(scene.keyframes, scene.duration_ms), {
            duration: scene.duration_ms,
            easing: 'linear',
            fill: 'forwards',
        }),
        ...playerTracks.map((track) => {
            const player = playerElement(track.side, track.player_id);
            return player?.animate(animationFrames(track.keyframes, scene.duration_ms), {
                duration: scene.duration_ms,
                easing: 'linear',
                fill: 'forwards',
            });
        }).filter(Boolean),
    ];
    await Promise.all(
        currentAnimations.map((animation) => animation.finished.catch(() => {})),
    );
    cancelAnimations();
    positionBall(finalKeyframe);
    playerTracks.forEach((track) => {
        positionPlayer(track.side, track.player_id, track.keyframes.at(-1));
    });
}

function resetSequence() {
    cancelAnimations();
    if (!sequenceData) return;
    positionState(sequenceData.initial_state);
    positionBall(sequenceData.scenes[0].keyframes[0]);
}

async function playSceneSequence() {
    if (!sequenceData?.scenes.length) return;

    resetSequence();
    ball.hidden = false;
    replayButton.disabled = true;
    replayButton.textContent = 'Sequência em curso';

    for (const [index, scene] of sequenceData.scenes.entries()) {
        sceneLabel.textContent = `Cena ${index + 1} / ${sequenceData.scenes.length}`;
        narration.textContent = scene.narration;
        const eventLabel = scene.event_type === 'carry' ? 'Condução' : 'Passe';
        phase.textContent = `${eventLabel} ${index + 1} de ${sequenceData.scenes.length}`;
        await animateScene(scene);
    }

    replayButton.disabled = false;
    replayButton.textContent = 'Repetir sequência';
    phase.textContent = 'Sequência concluída';
}

async function loadScene() {
    try {
        const response = await fetch(SCENE_ENDPOINT);
        if (!response.ok) throw new Error(`Cena indisponível: ${response.status}`);

        sequenceData = await response.json();
        narration.textContent = 'Passes e condução confirmados, reproduzidos em ordem.';
        resetSequence();
        replayButton.disabled = false;
        window.setTimeout(playSceneSequence, 350);
    } catch (error) {
        narration.textContent = 'Não foi possível carregar a cena de apresentação.';
        phase.textContent = 'Cena indisponível';
        console.error(error);
    }
}

replayButton.addEventListener('click', playSceneSequence);
loadScene();
