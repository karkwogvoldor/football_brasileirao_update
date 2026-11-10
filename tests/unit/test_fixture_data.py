from copy import deepcopy

import pytest

from brafoot.catalog.importer import (
    CatalogImportError,
    load_fixture_payload,
    validate_fixture_payload,
)


# Valida as invariantes completas do calendário oficial armazenado localmente.
def test_official_2026_fixture_data_has_complete_double_round_robin():
    payload = load_fixture_payload()

    validate_fixture_payload(payload)

    assert len(payload["clubs"]) == 20
    assert len(payload["fixtures"]) == 380


# Rejeita um calendário que repete uma referência de partida.
def test_fixture_validation_rejects_duplicate_reference():
    payload = deepcopy(load_fixture_payload())
    payload["fixtures"][1]["source_ref"] = payload["fixtures"][0]["source_ref"]

    with pytest.raises(CatalogImportError, match="Referência duplicada"):
        validate_fixture_payload(payload)
