"""Testes do Ingestion Engine — critérios de aceitação da spec 01, seção 8."""
import uuid
from datetime import date

from fastapi.testclient import TestClient

from app.main import app

CHAPTER_PAYLOAD = {
    "child_id": str(uuid.uuid4()),
    "subject": "Biologia",
    "school_start_date": "2026-08-10",
    "sources": [
        {
            "type": "text",
            "raw_ref": (
                "A célula é a unidade básica da vida.\n\n"
                "Todas as células possuem membrana plasmática.\n\n"
                "O núcleo contém o material genético da célula."
            ),
        }
    ],
}


def test_post_chapter_text_returns_ready():
    """Dado texto colado, quando processado, então status==ready e segments não-vazio."""
    with TestClient(app) as client:
        response = client.post("/chapters", json=CHAPTER_PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ready"
    assert len(body["segments"]) > 0
    assert "chapter_id" in body


def test_post_chapter_returns_chapter_id():
    """chapter_id é um UUID válido."""
    with TestClient(app) as client:
        response = client.post("/chapters", json=CHAPTER_PAYLOAD)
    body = response.json()
    uuid.UUID(body["chapter_id"])  # levanta ValueError se inválido


def test_get_chapter_returns_persisted_data():
    """Dado um capítulo criado, GET retorna status e segmentos."""
    with TestClient(app) as client:
        create = client.post("/chapters", json=CHAPTER_PAYLOAD)
        chapter_id = create.json()["chapter_id"]
        response = client.get(f"/chapters/{chapter_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["segments"] is not None


def test_school_start_date_persisted():
    """school_start_date é persistido e recuperável via GET."""
    with TestClient(app) as client:
        create = client.post("/chapters", json=CHAPTER_PAYLOAD)
        chapter_id = create.json()["chapter_id"]
        response = client.get(f"/chapters/{chapter_id}")
    assert response.json()["school_start_date"] == "2026-08-10"


def test_get_unknown_chapter_returns_404():
    with TestClient(app) as client:
        response = client.get(f"/chapters/{uuid.uuid4()}")
    assert response.status_code == 404


def test_post_chapter_image_source_returns_failed():
    """Dado source do tipo image, quando enviado, então status==failed e reason_code preenchido.

    OCR ainda não implementado — spec 01 seção 9 (pergunta em aberto sobre motor de OCR).
    """
    payload = {
        **CHAPTER_PAYLOAD,
        "sources": [{"type": "image", "raw_ref": "https://bucket.example.com/foto.jpg"}],
    }
    with TestClient(app) as client:
        response = client.post("/chapters", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "failed"
    assert body["reason_code"] == "not_implemented"


def test_post_chapter_link_source_returns_failed():
    """Dado source do tipo link, quando enviado, então status==failed (scraping não implementado)."""
    payload = {
        **CHAPTER_PAYLOAD,
        "sources": [{"type": "link", "raw_ref": "https://example.com/capitulo-1"}],
    }
    with TestClient(app) as client:
        response = client.post("/chapters", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "failed"
    assert body["reason_code"] == "not_implemented"


def test_text_with_single_paragraph_creates_one_segment():
    """Texto sem duplo-newline gera exatamente 1 segmento."""
    payload = {
        **CHAPTER_PAYLOAD,
        "sources": [{"type": "text", "raw_ref": "Conteúdo único sem quebras de parágrafo."}],
    }
    with TestClient(app) as client:
        response = client.post("/chapters", json=payload)
    assert response.json()["segments"] == ["Conteúdo único sem quebras de parágrafo."]


def test_text_segments_exclude_empty_lines():
    """Linhas em branco extras entre parágrafos não viram segmentos vazios."""
    payload = {
        **CHAPTER_PAYLOAD,
        "sources": [{"type": "text", "raw_ref": "Parágrafo A.\n\n\n\nParágrafo B."}],
    }
    with TestClient(app) as client:
        response = client.post("/chapters", json=payload)
    segments = response.json()["segments"]
    assert "" not in segments
    assert len(segments) == 2
