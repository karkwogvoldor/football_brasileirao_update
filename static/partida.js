const SCENE_ENDPOINT = '/api/v1/presentation/demo-sequence';

const ball = document.getElementById('sceneBall');
const narration = document.getElementById('sceneNarration');
const sceneLabel = document.getElementById('sceneLabel');
const replayButton = document.getElementById('replayScene');
const phase = document.querySelector('.match-phase');
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

let scenes = [];
let currentAnimation = null;

function positionBall(keyframe) {
    ball.style.left = `${keyframe.x}%`;
    ball.style.top = `${keyframe.y}%`;
}

async function animateScene(scene) {
    const finalKeyframe = scene.keyframes[scene.keyframes.length - 1];

    if (prefersReducedMotion.matches || typeof ball.animate !== 'function') {
        positionBall(finalKeyframe);
        return;
    }

    currentAnimation = ball.animate(
        scene.keyframes.map(keyframe => ({
            left: `${keyframe.x}%`,
            top: `${keyframe.y}%`,
            offset: keyframe.at_ms / scene.duration_ms,
        })),
        {
            duration: scene.duration_ms,
            easing: 'linear',
            fill: 'forwards',
        },
    );
    await currentAnimation.finished.catch(() => {});
    positionBall(finalKeyframe);
    currentAnimation.cancel();
    currentAnimation = null;
}

async function playSceneSequence() {
    if (!scenes.length) return;

    if (currentAnimation) currentAnimation.cancel();
    ball.hidden = false;
    replayButton.disabled = true;
    replayButton.textContent = 'Sequência em curso';
    positionBall(scenes[0].keyframes[0]);

    for (const [index, scene] of scenes.entries()) {
        sceneLabel.textContent = `Cena ${index + 1} / ${scenes.length}`;
        narration.textContent = scene.narration;
        phase.textContent = `Passe ${index + 1} de ${scenes.length}`;
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

        const sequence = await response.json();
        scenes = sequence.scenes;
        narration.textContent = 'Três passes confirmados, reproduzidos em ordem.';
        positionBall(scenes[0].keyframes[0]);
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
