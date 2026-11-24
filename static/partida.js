const SCENE_ENDPOINT = '/api/v1/presentation/demo-pass';

const ball = document.getElementById('sceneBall');
const narration = document.getElementById('sceneNarration');
const replayButton = document.getElementById('replayScene');
const phase = document.querySelector('.match-phase');
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

let scene = null;
let currentAnimation = null;

function positionBall(keyframe) {
    ball.style.left = `${keyframe.x}%`;
    ball.style.top = `${keyframe.y}%`;
}

async function playScene() {
    if (!scene) return;

    if (currentAnimation) currentAnimation.cancel();
    ball.hidden = false;
    replayButton.disabled = true;
    replayButton.textContent = 'Passe em curso';
    phase.textContent = 'Cena confirmada';

    if (prefersReducedMotion.matches || typeof ball.animate !== 'function') {
        positionBall(scene.keyframes[scene.keyframes.length - 1]);
    } else {
        currentAnimation = ball.animate(
            scene.keyframes.map(keyframe => ({
                left: `${keyframe.x}%`,
                top: `${keyframe.y}%`,
                offset: keyframe.at_ms / scene.duration_ms,
            })),
            {
                duration: scene.duration_ms,
                easing: 'cubic-bezier(0.33, 0.1, 0.2, 1)',
                fill: 'forwards',
            },
        );
        await currentAnimation.finished.catch(() => {});
    }

    replayButton.disabled = false;
    replayButton.textContent = 'Repetir passe';
    phase.textContent = 'Cena concluída';
}

async function loadScene() {
    try {
        const response = await fetch(SCENE_ENDPOINT);
        if (!response.ok) throw new Error(`Cena indisponível: ${response.status}`);

        scene = await response.json();
        narration.textContent = scene.narration;
        positionBall(scene.keyframes[0]);
        replayButton.disabled = false;
        window.setTimeout(playScene, 350);
    } catch (error) {
        narration.textContent = 'Não foi possível carregar a cena de apresentação.';
        phase.textContent = 'Cena indisponível';
        console.error(error);
    }
}

replayButton.addEventListener('click', playScene);
loadScene();
