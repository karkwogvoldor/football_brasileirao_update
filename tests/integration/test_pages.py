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
    assert len(catalog["scenarios"]) == 16
    assert len({scenario["id"] for scenario in catalog["scenarios"]}) == 16
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
        "movement-offside-trap",
        "movement-offside-trap-success",
        "movement-high-press",
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


def _scenarios_by_id(client):
    return {
        scenario["id"]: scenario
        for scenario in client.get("/api/v1/dev/presentation-scenes").json()["scenarios"]
    }


def _state_positions(state):
    return {
        (player["side"], player["player_id"]): (player["x"], player["y"])
        for player in state["players"]
    }


# Nenhum jogador das cenas novas ou revisadas excede uma velocidade humana de corrida (8,5 m/s).
def test_new_and_revised_scenes_keep_human_running_speeds(client):
    scenarios = _scenarios_by_id(client)
    reviewed = (
        "movement-switch-of-play",
        "ball-cross-far-post",
        "movement-offside-trap",
        "ball-goal-kick-short",
        "ball-one-two",
        "movement-offside-trap-success",
        "ball-overlap-fullback",
        "ball-counter-attack",
        "movement-high-press",
    )

    for scenario_id in reviewed:
        for scene in scenarios[scenario_id]["scenes"]:
            seconds = scene["duration_ms"] / 1000
            for track in scene["player_tracks"]:
                start, end = track["keyframes"][0], track["keyframes"][-1]
                meters = (
                    ((end["x"] - start["x"]) * 1.05) ** 2
                    + ((end["y"] - start["y"]) * 0.68) ** 2
                ) ** 0.5
                assert meters / seconds <= 8.5, (scenario_id, track["player_id"])


# A inversão de jogo revisada: lateral acompanha para a frente, goleiros quase parados e movimento suave.
def test_switch_of_play_revision_is_smoother_with_forward_fullback(client):
    scenario = _scenarios_by_id(client)["movement-switch-of-play"]
    initial = _state_positions(scenario["initial_state"])
    final = _state_positions(scenario["final_state"])

    assert scenario["version"] == 2
    assert scenario["scenes"][0]["duration_ms"] >= 2400  # mais lenta e suave
    assert final[("home", 6)][0] > initial[("home", 6)][0]  # lateral avança após o lançamento
    assert final[("home", 7)][0] > initial[("home", 7)][0]  # atacantes sobem levemente
    assert abs(final[("home", 1)][1] - initial[("home", 1)][1]) <= 6  # goleiro não varre o campo


# O cruzamento termina com a bola no segundo pau, um atacante no primeiro pau e a zaga dentro da área.
def test_cross_scene_occupies_near_far_post_and_keeps_defense_in_box(client):
    scenario = _scenarios_by_id(client)["ball-cross-far-post"]
    final = _state_positions(scenario["final_state"])
    ball = scenario["scenes"][0]["keyframes"][-1]

    assert scenario["scenes"][0]["event_type"] == "cross"
    assert (ball["x"], ball["y"]) == final[("home", 7)]  # bola chega ao atacante do segundo pau
    assert final[("home", 7)][1] < 50 < final[("home", 9)][1]  # lados opostos do gol
    assert final[("home", 9)][0] >= 94  # primeiro pau, junto da pequena área
    assert all(final[("away", pid)][0] >= 84 for pid in (2, 3, 4, 6))  # zaga na grande área
    assert 90 <= final[("away", 1)][0] <= 96


# Na linha ineficiente o atacante estava na linha no passe, não é impedimento e ele escapa livre.
def test_ineffective_offside_line_leaves_striker_onside_and_free(client):
    scenario = _scenarios_by_id(client)["movement-offside-trap"]
    initial = _state_positions(scenario["initial_state"])
    final = _state_positions(scenario["final_state"])
    line_at_pass = {initial[("away", pid)][0] for pid in (2, 3, 4, 6)}

    assert scenario["version"] == 2
    assert scenario["title"] == "Linha de impedimento ineficiente"
    assert len(line_at_pass) == 1
    assert initial[("home", 9)][0] < line_at_pass.pop()  # no momento do passe está em jogo
    assert final[("home", 9)][0] > final[("away", 3)][0]  # termina livre, nas costas da zaga
    assert "legal" in scenario["scenes"][0]["narration"]


# Na linha bem-sucedida a zaga sobe junta e, no momento do passe, o centroavante já está além dela.
def test_successful_offside_line_catches_striker_beyond_the_line(client):
    scenario = _scenarios_by_id(client)["movement-offside-trap-success"]
    rise, offside_pass = scenario["scenes"]
    line_after_rise = {
        track["keyframes"][-1]["x"]
        for track in rise["player_tracks"]
        if track["side"] == "away" and track["player_id"] in (2, 3, 4, 6)
    }
    striker_after_rise = next(
        track["keyframes"][-1]["x"]
        for track in rise["player_tracks"]
        if track["side"] == "home" and track["player_id"] == 9
    )
    line_start = {
        track["keyframes"][0]["x"]
        for track in rise["player_tracks"]
        if track["side"] == "away" and track["player_id"] in (2, 3, 4, 6)
    }

    assert scenario["title"] == "Linha de impedimento bem-sucedida"
    assert (rise["event_type"], offside_pass["event_type"]) == ("carry", "pass")
    assert len(line_after_rise) == 1 and len(line_start) == 1  # sobe em linha reta
    assert line_after_rise.pop() < line_start.pop()
    assert striker_after_rise > min(
        track["keyframes"][-1]["x"]
        for track in rise["player_tracks"]
        if track["side"] == "away" and track["player_id"] in (2, 3, 4, 6)
    )  # no momento do passe, além da linha
    assert "impedimento" in offside_pass["narration"]


# Na ultrapassagem o marcador acompanha o ponta para dentro e o lateral recebe por fora, à frente da bola.
def test_overlap_scene_frees_the_fullback_on_the_outside(client):
    scenario = _scenarios_by_id(client)["ball-overlap-fullback"]
    cut, give = scenario["scenes"]
    initial = _state_positions(scenario["initial_state"])
    final = _state_positions(scenario["final_state"])

    assert [cut["participant_ids"], give["participant_ids"]] == [[11], [11, 6]]
    assert final[("home", 6)][0] > initial[("home", 11)][0]  # lateral ultrapassa o ponta
    assert final[("home", 6)][1] > 85  # por fora, perto da linha lateral
    cut_end = cut["keyframes"][-1]
    assert cut_end["y"] < initial[("home", 11)][1]  # ponta corta para dentro
    away_marker_end = next(
        track["keyframes"][-1]
        for track in cut["player_tracks"]
        if track["side"] == "away" and track["player_id"] == 2
    )
    assert away_marker_end["y"] < initial[("away", 2)][1]  # marcador acompanha para dentro
    ball_end = give["keyframes"][-1]
    assert (ball_end["x"], ball_end["y"]) == final[("home", 6)]


# No contra-ataque a bola sai pelo meio, abre para a ponta e termina em finalização com a área ocupada.
def test_counter_attack_runs_diagonals_and_finishes_with_box_support(client):
    scenario = _scenarios_by_id(client)["ball-counter-attack"]
    passes_and_shot = scenario["scenes"]
    initial = _state_positions(scenario["initial_state"])
    final = _state_positions(scenario["final_state"])

    assert [scene["event_type"] for scene in passes_and_shot] == ["pass", "pass", "shot"]
    assert passes_and_shot[-1]["keyframes"][-1]["x"] >= 98  # chuta ao gol
    assert final[("home", 9)][0] >= 80 and final[("home", 7)][0] >= 80  # área ocupada
    assert final[("home", 7)][1] < 50 < final[("home", 11)][1]  # pontas em lados opostos
    assert final[("away", 3)][0] > initial[("away", 3)][0]  # defesa recua
    first_ball = passes_and_shot[0]["keyframes"]
    assert first_ball[-1]["x"] - first_ball[0]["x"] > 10  # passe vertical


# Na pressão alta o gatilho é o passe do adversário e a casa sobe junta, com a zaga em linha única.
def test_high_press_moves_the_team_up_together_after_a_back_pass(client):
    scenario = _scenarios_by_id(client)["movement-high-press"]
    initial = _state_positions(scenario["initial_state"])
    final = _state_positions(scenario["final_state"])
    scene = scenario["scenes"][0]
    line_shift = {
        round(final[("home", pid)][0] - initial[("home", pid)][0], 6) for pid in (2, 3, 4, 6)
    }

    assert scene["team_side"] == "away" and scene["participant_ids"] == [3, 1]
    assert len(line_shift) == 1 and line_shift.pop() > 0  # zaga sobe como uma linha
    assert final[("home", 9)][0] - initial[("home", 9)][0] > 8  # centroavante pressiona o goleiro
    assert all(final[("home", pid)][0] > initial[("home", pid)][0] for pid in range(2, 12))
    assert 90 <= final[("away", 1)][0] <= 96


# No tiro de meta curto o goleiro toca para o zagueiro aberto na área e o adversário pressiona.
def test_short_goal_kick_builds_from_the_back_under_pressure(client):
    scenario = _scenarios_by_id(client)["ball-goal-kick-short"]
    initial = _state_positions(scenario["initial_state"])
    final = _state_positions(scenario["final_state"])

    assert scenario["scenes"][0]["participant_ids"] == [1, 4]
    assert final[("home", 4)][0] <= 16  # receptor dentro da área
    assert final[("home", 4)][1] > 60  # aberto
    assert final[("away", 9)][0] < initial[("away", 9)][0]  # adversário fecha a linha de passe
    assert 4 <= final[("home", 1)][0] <= 10


# Na tabela a bola volta ao meia, que termina à frente do ponto onde passou.
def test_one_two_returns_ball_to_the_runner_ahead_of_the_passer(client):
    scenario = _scenarios_by_id(client)["ball-one-two"]
    first, second = scenario["scenes"]
    initial = _state_positions(scenario["initial_state"])
    final = _state_positions(scenario["final_state"])

    assert [first["participant_ids"], second["participant_ids"]] == [[8, 9], [9, 8]]
    start, end = second["keyframes"][0], first["keyframes"][-1]
    assert (start["x"], start["y"]) == (end["x"], end["y"])  # sem teletransporte da bola
    assert second["keyframes"][-1]["x"] == final[("home", 8)][0]
    assert final[("home", 8)][0] > initial[("home", 9)][0]  # recebe além da posição do parceiro
