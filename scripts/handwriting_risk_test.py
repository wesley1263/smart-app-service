#!/usr/bin/env python3
"""
Teste de risco: valida se um modelo de visão consegue ler manuscrito infantil
com taxa de acerto suficiente para o Evidence Engine.

Uso:
    python scripts/handwriting_risk_test.py \\
        --input fotos/ \\
        --gabarito gabarito.json \\
        [--threshold 0.65] \\
        [--model claude-haiku-4-5-20251001] \\
        [--output resultado.json]

Formato do gabarito (JSON):
    {
      "foto01.jpg": {
        "node": "Célula",
        "expected_keywords": ["membrana plasmática", "núcleo", "mitocôndria"]
      }
    }

Ver tasks/TASK-000-teste-risco-manuscrito.md e specs/03-evidence-engine.md.
Este script NÃO depende de nenhum código de app/.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_THRESHOLD = 0.65


# ── Estruturas de dados ────────────────────────────────────────────────────────

@dataclass
class PhotoResult:
    filename: str
    node: str
    expected: list[str]
    found: list[str] = field(default_factory=list)
    not_found: list[str] = field(default_factory=list)
    match_score: float = 0.0
    passed: bool = False
    notes: str = ""
    error: str = ""


# ── I/O ───────────────────────────────────────────────────────────────────────

def load_gabarito(path: Path) -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for fname, entry in data.items():
        if "expected_keywords" not in entry:
            raise ValueError(f"Gabarito: entrada '{fname}' sem 'expected_keywords'.")
        if not entry["expected_keywords"]:
            raise ValueError(f"Gabarito: '{fname}' tem expected_keywords vazio.")
    return data


def encode_image(path: Path) -> tuple[str, str]:
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    media_type = media_types.get(path.suffix.lower(), "image/jpeg")
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


# ── Prompt ─────────────────────────────────────────────────────────────────────

def build_prompt(node: str, expected_keywords: list[str]) -> str:
    kw_list = "\n".join(f"  - {kw}" for kw in expected_keywords)
    return f"""Você está validando o caderno/mindmap manuscrito de um estudante.

Conceito estudado: "{node}"

Palavras-chave esperadas:
{kw_list}

Observe atentamente o conteúdo manuscrito na imagem.

Para cada palavra-chave, verifique se ela aparece na escrita (diretamente ou por sinônimos/variações equivalentes). Seja generoso: grafias alternativas e conceitos expressos com palavras diferentes contam.

Responda SOMENTE com um objeto JSON neste formato exato, sem markdown:
{{
  "found": ["palavras-chave encontradas na imagem"],
  "not_found": ["palavras-chave não encontradas"],
  "notes": "observação breve sobre qualidade ou legibilidade da imagem"
}}"""


# ── Validação de uma foto ──────────────────────────────────────────────────────

def _normalize(keywords: list[str]) -> dict[str, str]:
    """Mapeia versão lowercase → original para match case-insensitive."""
    return {kw.lower().strip(): kw for kw in keywords}


def validate_photo(
    photo_path: Path,
    node: str,
    expected_keywords: list[str],
    client: object,
    model: str,
) -> PhotoResult:
    base = PhotoResult(
        filename=photo_path.name,
        node=node,
        expected=expected_keywords,
        not_found=list(expected_keywords),
    )

    try:
        image_data, media_type = encode_image(photo_path)
    except Exception as exc:
        base.error = f"Erro ao ler imagem: {exc}"
        return base

    try:
        response = client.messages.create(  # type: ignore[attr-defined]
            model=model,
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": build_prompt(node, expected_keywords)},
                    ],
                }
            ],
        )
        raw = response.content[0].text.strip()

        # Remove bloco markdown caso o modelo devolva ```json ... ```
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1][4:] if parts[1].startswith("json") else parts[1]

        parsed = json.loads(raw)

    except json.JSONDecodeError as exc:
        base.error = f"Resposta do modelo não é JSON válido: {exc}"
        return base
    except Exception as exc:
        base.error = f"Erro na chamada ao modelo: {exc}"
        return base

    # Match case-insensitive entre o que o modelo retornou e o gabarito
    expected_map = _normalize(expected_keywords)
    found_originals: list[str] = []
    for kw in parsed.get("found", []):
        original = expected_map.get(kw.lower().strip())
        if original and original not in found_originals:
            found_originals.append(original)

    not_found = [kw for kw in expected_keywords if kw not in found_originals]
    match_score = len(found_originals) / len(expected_keywords) if expected_keywords else 0.0

    base.found = found_originals
    base.not_found = not_found
    base.match_score = match_score
    base.notes = parsed.get("notes", "")
    return base


# ── Relatório ─────────────────────────────────────────────────────────────────

def print_report(results: list[PhotoResult], threshold: float, model: str) -> None:
    errors = [r for r in results if r.error]
    valid = [r for r in results if not r.error]
    passed = [r for r in valid if r.passed]
    failed = [r for r in valid if not r.passed]

    sep = "─" * 62
    print(f"\n{sep}")
    print("  RELATÓRIO — Teste de risco: leitura de manuscrito infantil")
    print(sep)
    print(f"  Modelo     : {model}")
    print(f"  Threshold  : {threshold:.0%}")
    print(f"  Processadas: {len(results)}  |  válidas: {len(valid)}  |  erros: {len(errors)}")
    print(sep)

    if valid:
        avg = sum(r.match_score for r in valid) / len(valid)
        rate = len(passed) / len(valid)
        print(f"  Score médio  : {avg:.1%}")
        print(f"  Taxa de aprovação : {len(passed)}/{len(valid)} = {rate:.1%}")
        print()

    if passed:
        print(f"  ✓ APROVADAS ({len(passed)})")
        for r in passed:
            print(f"    {r.filename:<32} {r.match_score:.0%}  [{r.node}]")

    if failed:
        print()
        print(f"  ✗ ABAIXO DO THRESHOLD ({len(failed)})")
        for r in failed:
            print(f"    {r.filename:<32} {r.match_score:.0%}  [{r.node}]")
            if r.not_found:
                print(f"      não encontrado : {', '.join(r.not_found)}")
            if r.notes:
                print(f"      nota do modelo : {r.notes}")

    if errors:
        print()
        print(f"  ⚠ ERROS ({len(errors)})")
        for r in errors:
            print(f"    {r.filename} — {r.error}")

    print(sep)

    if not valid:
        conclusion = "Nenhuma foto processada. Verifique ANTHROPIC_API_KEY e as imagens."
    else:
        rate = len(passed) / len(valid)
        if rate >= 0.80:
            conclusion = "✓ VIÁVEL — modelo adequado para o Evidence Engine."
        elif rate >= 0.60:
            conclusion = "⚠ MARGINAL — considere aumentar threshold ou testar outro modelo."
        else:
            conclusion = "✗ INVIÁVEL — taxa insuficiente. Revisar spec 03, seção 9."

    print(f"\n  CONCLUSÃO: {conclusion}\n")


def save_json_report(
    results: list[PhotoResult],
    output_path: Path,
    threshold: float,
    model: str,
) -> None:
    valid = [r for r in results if not r.error]
    avg = sum(r.match_score for r in valid) / len(valid) if valid else 0.0
    data = {
        "model": model,
        "threshold": threshold,
        "summary": {
            "total": len(results),
            "valid": len(valid),
            "passed": sum(1 for r in valid if r.passed),
            "failed": sum(1 for r in valid if not r.passed),
            "errors": sum(1 for r in results if r.error),
            "avg_score": round(avg, 4),
        },
        "results": [
            {
                "filename": r.filename,
                "node": r.node,
                "match_score": round(r.match_score, 4),
                "passed": r.passed,
                "found": r.found,
                "not_found": r.not_found,
                "notes": r.notes,
                "error": r.error,
            }
            for r in results
        ],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Relatório JSON salvo em: {output_path}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Valida se um modelo de visão lê manuscrito infantil com acurácia suficiente.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--input", required=True, metavar="DIR", help="Diretório com as fotos")
    parser.add_argument("--gabarito", required=True, metavar="FILE", help="JSON com keywords esperadas por foto")
    parser.add_argument(
        "--threshold", type=float, default=DEFAULT_THRESHOLD,
        help=f"Match mínimo para aprovação (default: {DEFAULT_THRESHOLD})",
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"Modelo de visão a testar (default: {DEFAULT_MODEL})",
    )
    parser.add_argument("--output", metavar="FILE", help="Salvar relatório detalhado em JSON")
    args = parser.parse_args()

    input_dir = Path(args.input)
    gabarito_path = Path(args.gabarito)

    if not input_dir.is_dir():
        print(f"Erro: '{input_dir}' não é um diretório.", file=sys.stderr)
        sys.exit(1)
    if not gabarito_path.is_file():
        print(f"Erro: gabarito '{gabarito_path}' não encontrado.", file=sys.stderr)
        sys.exit(1)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Erro: variável de ambiente ANTHROPIC_API_KEY não definida.", file=sys.stderr)
        sys.exit(1)

    try:
        import anthropic
    except ImportError:
        print("Erro: pacote 'anthropic' não instalado. Execute: pip install anthropic", file=sys.stderr)
        sys.exit(1)

    try:
        gabarito = load_gabarito(gabarito_path)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Erro no gabarito: {exc}", file=sys.stderr)
        sys.exit(1)

    photos = sorted(p for p in input_dir.iterdir() if p.suffix.lower() in SUPPORTED_EXTENSIONS)
    if not photos:
        exts = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        print(f"Nenhuma foto encontrada em '{input_dir}' (extensões aceitas: {exts}).", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print(f"\nProcessando {len(photos)} foto(s) com '{args.model}' (threshold={args.threshold:.0%})...")

    results: list[PhotoResult] = []
    for i, photo_path in enumerate(photos, 1):
        entry = gabarito.get(photo_path.name)
        if not entry:
            print(f"  [{i}/{len(photos)}] {photo_path.name} — sem entrada no gabarito, ignorando.")
            continue

        print(f"  [{i}/{len(photos)}] {photo_path.name} ...", end=" ", flush=True)

        result = validate_photo(
            photo_path,
            node=entry.get("node", ""),
            expected_keywords=entry["expected_keywords"],
            client=client,
            model=args.model,
        )
        result.passed = result.match_score >= args.threshold
        results.append(result)

        if result.error:
            print(f"ERRO: {result.error[:60]}")
        else:
            print(f"score={result.match_score:.0%} {'✓' if result.passed else '✗'}")

        # Pausa entre chamadas para evitar rate limit
        if i < len(photos):
            time.sleep(0.5)

    if not results:
        print("Nenhuma foto do gabarito encontrada no diretório.", file=sys.stderr)
        sys.exit(1)

    print_report(results, threshold=args.threshold, model=args.model)

    if args.output:
        save_json_report(results, Path(args.output), threshold=args.threshold, model=args.model)


if __name__ == "__main__":
    main()
