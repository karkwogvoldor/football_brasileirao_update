import pytest
from html.parser import HTMLParser

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect

from main import create_app


pytestmark = pytest.mark.integration


class ImageSourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            source = dict(attrs).get("src")
            if source:
                self.sources.append(source)


class MatchPageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.players = []
        self.stylesheets = []
        self.scripts = []
        self.pitch_labels = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = attributes.get("class", "").split()
        if tag == "article" and "match-player" in classes:
            style = dict(
                declaration.strip().split(":", 1)
                for declaration in attributes["style"].split(";")
                if declaration.strip()
            )
            self.players.append(
                {
                    "team": attributes["data-team"],
                    "x": int(style["--x"]),
                    "y": int(style["--y"]),
                }
            )
        if tag == "link" and attributes.get("rel") == "stylesheet":
            self.stylesheets.append(attributes.get("href"))
        if tag == "script" and attributes.get("src"):
            self.scripts.append(attributes["src"])
        if tag == "svg" and "match-pitch-lines" in classes:
            self.pitch_labels.append(attributes.get("aria-label"))


# Verifica se a página inicial responde com HTML.
def test_home_page_is_available(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


# Verifica se a rota de clube continua servindo sua página base.
def test_club_page_is_currently_static(client):
    response = client.get("/clube/999999")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


# Renderiza duas formações completas, normalizadas e espelhadas na página da partida.
def test_match_page_renders_two_static_mirrored_formations(client):
    response = client.get("/partida")
    parser = MatchPageParser()
    parser.feed(response.text)

    home_players = [player for player in parser.players if player["team"] == "home"]
    away_players = [player for player in parser.players if player["team"] == "away"]

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert len(home_players) == 11
    assert len(away_players) == 11
    assert all(0 <= player["x"] <= 100 for player in parser.players)
    assert all(0 <= player["y"] <= 100 for player in parser.players)
    assert [player["x"] for player in away_players] == [
        100 - player["x"] for player in home_players
    ]
    assert [player["y"] for player in away_players] == [
        player["y"] for player in home_players
    ]
    assert parser.pitch_labels == ["Campo de futebol com duas formações estáticas"]


# Serve a folha de estilos própria sem depender do editor de escalação legado.
def test_match_page_has_available_dedicated_stylesheet(client):
    response = client.get("/partida")
    parser = MatchPageParser()
    parser.feed(response.text)

    assert "/static/partida.css" in parser.stylesheets
    stylesheet = client.get("/static/partida.css")
    assert stylesheet.status_code == 200
    assert stylesheet.headers["content-type"].startswith("text/css")


# Expõe eventos visuais encadeados sem consultar banco ou alterar a partida.
def test_demo_presentation_sequence_endpoint_is_deterministic(client):
    first_response = client.get("/api/v1/presentation/demo-sequence")
    second_response = client.get("/api/v1/presentation/demo-sequence")
    sequence = first_response.json()

    assert first_response.status_code == 200
    assert second_response.json() == sequence
    assert sequence["presentation_version"] == "2026.1"
    assert [scene["participant_ids"] for scene in sequence["scenes"]] == [
        [8, 9],
        [9, 7],
        [7, 10],
        [10],
        [10, 11],
        [11],
    ]
    assert [scene["event_type"] for scene in sequence["scenes"]] == [
        "pass",
        "pass",
        "pass",
        "carry",
        "pass",
        "shot",
    ]
    assert sequence["scenes"][3]["player_tracks"][0]["player_id"] == 10
    assert sequence["scenes"][3]["player_tracks"][0]["keyframes"] == sequence[
        "scenes"
    ][3]["keyframes"]
    assert all(len(scene["player_tracks"]) == 22 for scene in sequence["scenes"])
    assert sequence["initial_state"]["ball_holder_id"] == 8
    assert sequence["final_state"]["ball_holder_id"] is None
    assert sequence["final_state"]["ball_position"] == {"x": 98, "y": 55}
    for current, following in zip(sequence["scenes"], sequence["scenes"][1:]):
        assert current["keyframes"][-1] == {
            **following["keyframes"][0],
            "at_ms": current["duration_ms"],
        }


# Carrega o reprodutor dedicado da cena sem reutilizar o editor legado.
def test_match_page_has_available_presentation_script(client):
    response = client.get("/partida")
    parser = MatchPageParser()
    parser.feed(response.text)

    assert "/static/partida.js" in parser.scripts
    script = client.get("/static/partida.js")
    assert script.status_code == 200
    assert "demo-sequence" in script.text


# Consome as coordenadas planas dos jogadores exatamente como o snapshot as entrega.
def test_presentation_script_reads_flat_player_snapshot(client):
    sequence = client.get("/api/v1/presentation/demo-sequence").json()
    script = client.get("/static/partida.js").text

    assert set(sequence["initial_state"]["players"][0]) == {
        "side",
        "player_id",
        "x",
        "y",
    }
    assert "positionPlayer(player.side, player.player_id, player);" in script
    assert "player.position" not in script


# Serve o laboratório de cenas com seus recursos dedicados de apresentação.
def test_developer_scene_lab_is_available(client):
    response = client.get("/dev/cenas")
    parser = MatchPageParser()
    parser.feed(response.text)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "/static/dev-cenas.css" in parser.stylesheets
    assert "/static/dev-cenas.js" in parser.scripts
    assert client.get("/static/dev-cenas.css").status_code == 200
    assert client.get("/static/dev-cenas.js").status_code == 200


# Expõe cenários versionados, agrupados e determinísticos para revisão visual.
def test_developer_scene_catalog_is_grouped_and_deterministic(client):
    first = client.get("/api/v1/dev/presentation-scenes")
    second = client.get("/api/v1/dev/presentation-scenes")
    catalog = first.json()

    assert first.status_code == 200
    assert second.json() == catalog
    assert [group["id"] for group in catalog["groups"]] == [
        "ball",
        "movement",
        "composite",
    ]
    assert len(catalog["scenarios"]) == 8
    assert len({scenario["id"] for scenario in catalog["scenarios"]}) == 8
    assert all(
        len(scenario["initial_state"]["players"]) == 22
        and scenario["scenes"]
        and scenario["status"] == "pending"
        for scenario in catalog["scenarios"]
    )
    movement_ids = {
        scenario["id"]
        for scenario in catalog["scenarios"]
        if scenario["category"] == "movement"
    }
    assert movement_ids == {
        "movement-switch-of-play",
        "movement-goalkeeper-adjustment",
        "movement-interception-attempt",
    }
    composite = next(
        scenario
        for scenario in catalog["scenarios"]
        if scenario["id"] == "composite-attacking-sequence"
    )
    assert len(composite["scenes"]) == 6


# Persiste o rascunho enquanto ele é digitado antes de trocar de cenário.
def test_developer_scene_review_note_is_saved_on_input(client):
    script = client.get("/static/dev-cenas.js")

    assert script.status_code == 200
    assert "function saveReviewDraft()" in script.text
    assert "reviewNote.addEventListener('input', saveReviewDraft);" in script.text


# Separa aprovadas e bloqueia feedback somente após salvamento explícito.
def test_developer_scene_lab_has_review_views_and_feedback_lock(client):
    page = client.get("/dev/cenas")
    script = client.get("/static/dev-cenas.js")

    assert 'id="catalogReviewTab"' in page.text
    assert 'id="catalogApprovedTab"' in page.text
    assert 'id="saveReviewNote"' in page.text
    assert 'id="editReviewNote"' in page.text
    assert "function setCatalogView(view)" in script.text
    assert "function lockReviewNote()" in script.text
    assert "function unlockReviewNote()" in script.text


# Exporta revisões locais e destaca cenas modificadas que aguardam nova análise.
def test_developer_scene_lab_exports_reviews_and_marks_ready_scenes(client):
    page = client.get("/dev/cenas")
    script = client.get("/static/dev-cenas.js")

    assert 'id="exportSceneReviews"' in page.text
    assert 'data-review="ready_for_review"' in page.text
    assert "function exportSceneReviews()" in script.text
    assert "ready_for_review" in script.text


# Verifica se todos os escudos exibidos na página inicial existem e são servidos como imagem.
def test_home_team_badges_are_available(client):
    page = client.get("/")
    parser = ImageSourceParser()
    parser.feed(page.text)

    assert len(parser.sources) == 20
    for source in parser.sources:
        image = client.get(source)
        assert image.status_code == 200, source
        assert image.headers["content-type"].startswith("image/"), source
        assert image.content, source


# Garante que o startup padrão não cria tabelas fora do controle do Alembic.
def test_default_application_startup_does_not_create_database_schema(tmp_path):
    database_path = tmp_path / "startup_test.db"
    engine = create_engine(f"sqlite+pysqlite:///{database_path.as_posix()}")
    application = create_app(database_engine=engine)

    with TestClient(application) as test_client:
        assert test_client.get("/").status_code == 200

    assert inspect(engine).get_table_names() == []
    engine.dispose()


# As duas cenas corrigidas sobem de versão e respeitam goleiro, zagueiros e corridas pedidas na revisão.
def test_revised_scenes_apply_review_feedback(client):
    scenarios = {
        scenario["id"]: scenario
        for scenario in client.get("/api/v1/dev/presentation-scenes").json()["scenarios"]
    }

    def final(scenario, side, player_id):
        return next(
            player
            for player in scenario["final_state"]["players"]
            if player["side"] == side and player["player_id"] == player_id
        )

    carry = scenarios["carry-right-channel"]
    assert carry["version"] == 3
    assert 4 <= final(carry, "home", 1)["x"] <= 10
    assert 90 <= final(carry, "away", 1)["x"] <= 96
    assert all(final(carry, "away", pid)["x"] <= 83 for pid in (2, 3, 4, 6))

    assert final(carry, "home", 7)["y"] < 20  # ponta esquerda abre o campo
    assert final(carry, "home", 11)["y"] > 80  # ponta direita repete a abertura, espelhada
    assert final(carry, "home", 11)["x"] == final(carry, "home", 7)["x"]  # mesmo avanço
    assert final(carry, "home", 9)["x"] > 42  # centroavante ataca o espaço
    assert "movement-collective-shift-right" not in scenarios  # cena excluída na revisão


# A inversão de jogo lança do lateral direito ao esquerdo e desloca os blocos para o outro lado.
def test_switch_of_play_moves_blocks_from_right_to_left(client):
    scenario = next(
        item
        for item in client.get("/api/v1/dev/presentation-scenes").json()["scenarios"]
        if item["id"] == "movement-switch-of-play"
    )

    def mean_y(state, side):
        ys = [p["y"] for p in state["players"] if p["side"] == side and p["player_id"] != 2]
        return sum(ys) / len(ys)

    pass_scene = scenario["scenes"][0]
    assert pass_scene["participant_ids"] == [6, 2]
    assert scenario["category"] == "movement"
    initial = {(p["side"], p["player_id"]): p for p in scenario["initial_state"]["players"]}
    assert initial[("home", 6)]["y"] > 85 and initial[("home", 2)]["y"] < 15  # laterais abertos
    for side in ("home", "away"):
        assert mean_y(scenario["initial_state"], side) > 60  # bloco pendendo para a direita
        assert mean_y(scenario["final_state"], side) < mean_y(scenario["initial_state"], side) - 10


# A cena composta avança sem vai e vem, com as linhas encaixadas e a zaga como unidade própria.
def test_composite_scene_interlocks_lines_without_backward_drift(client):
    scenarios = {
        scenario["id"]: scenario
        for scenario in client.get("/api/v1/dev/presentation-scenes").json()["scenarios"]
    }
    composite = scenarios["composite-attacking-sequence"]
    assert composite["version"] == 2

    def positions(state):
        return {
            (player["side"], player["player_id"]): player["x"]
            for player in state["players"]
        }

    initial, final = positions(composite["initial_state"]), positions(composite["final_state"])
    previous = initial
    for scene in composite["scenes"]:
        current = {
            (track["side"], track["player_id"]): track["keyframes"][-1]["x"]
            for track in scene["player_tracks"]
        }
        assert all(current[key] >= previous[key] for key in current)  # sem vai e vem
        previous = current
    assert final[("home", 9)] > final[("away", 9)]  # linhas dos times se encaixam
    assert 4 <= final[("home", 1)] <= 10 and 90 <= final[("away", 1)] <= 96
    home_line = {round(final[("home", pid)] - initial[("home", pid)], 6) for pid in (2, 3, 4, 6)}
    assert len(home_line) == 1  # zaga move-se como uma linha única
    assert all(final[("away", pid)] <= 83 for pid in (2, 3, 4, 6))


# Na finalização o goleiro visitante fica fora do gol e o visitante 11 não é espelhado do artilheiro.
def test_shot_scene_keeps_goalkeeper_out_of_goal(client):
    shot = next(
        scenario
        for scenario in client.get("/api/v1/dev/presentation-scenes").json()["scenarios"]
        if scenario["id"] == "shot-near-area"
    )
    final = {
        (player["side"], player["player_id"]): player
        for player in shot["final_state"]["players"]
    }

    assert shot["version"] == 2
    assert 90 <= final[("away", 1)]["x"] <= 96
    assert 4 <= final[("home", 1)]["x"] <= 10
    initial_away_11 = next(
        player
        for player in shot["initial_state"]["players"]
        if player["side"] == "away" and player["player_id"] == 11
    )
    assert initial_away_11["x"] > 50  # fica no campo de ataque do time da casa, não em (24,28)
