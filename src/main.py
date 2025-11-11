"""Command line interface for the experience analyzer."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import List

from experience_analyzer.comparer import compare_certificates_with_cv
from experience_analyzer.models import ExperienceRecord
from experience_analyzer.pdf_extractor import extract_text_from_pdf
from experience_analyzer.report import build_table
from experience_analyzer.text_parser import parse_experiences_from_text

logger = logging.getLogger(__name__)


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="[%(levelname)s] %(message)s",
    )


def _load_experiences(paths: List[Path], source_label: str) -> List[ExperienceRecord]:
    experiences: List[ExperienceRecord] = []
    for path in paths:
        logger.info("Leyendo %s", path)
        extraction = extract_text_from_pdf(path)
        logger.info("Texto extraído mediante %s", extraction.method)
        parsed = parse_experiences_from_text(extraction.text, source=f"{source_label}: {path.name}")
        if not parsed:
            logger.warning("No se encontraron experiencias en %s", path)
        experiences.extend(parsed)
    return experiences


def main() -> None:
    parser = argparse.ArgumentParser(description="Analiza certificados laborales y hoja de vida")
    parser.add_argument("certificates", nargs="+", type=Path, help="Rutas de los PDF de certificaciones")
    parser.add_argument("--cv", required=True, type=Path, help="Ruta del PDF de la hoja de vida")
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Ruta de archivo JSON opcional para guardar los resultados estructurados",
    )
    parser.add_argument("--verbose", action="store_true", help="Muestra información detallada")

    args = parser.parse_args()
    _configure_logging(args.verbose)

    certificate_records = _load_experiences(args.certificates, "Certificado")
    cv_records = _load_experiences([args.cv], "Hoja de vida")

    comparisons = compare_certificates_with_cv(certificate_records, cv_records)
    table = build_table(comparisons)
    print(table)

    if args.output_json:
        payload = [
            {
                "fuente": comparison.certificate.source,
                "entidad": comparison.certificate.employer,
                "ingreso_certificado": comparison.certificate.start_date.isoformat()
                if comparison.certificate.start_date
                else None,
                "retiro_certificado": comparison.certificate.end_date.isoformat()
                if comparison.certificate.end_date
                else None,
                "fecha_expedicion": comparison.certificate.issue_date.isoformat()
                if comparison.certificate.issue_date
                else None,
                "fin_contabilizado": comparison.certificate.effective_end_date.isoformat()
                if comparison.certificate.effective_end_date
                else None,
                "dias_experiencia": comparison.certificate.experience_days,
                "coincide_hv": comparison.start_date_match and comparison.cv_entry is not None,
                "entidad_hv": comparison.cv_entry.employer if comparison.cv_entry else None,
                "ingreso_hv": comparison.cv_entry.start_date.isoformat()
                if comparison.cv_entry and comparison.cv_entry.start_date
                else None,
                "retiro_hv": comparison.cv_entry.end_date.isoformat()
                if comparison.cv_entry and comparison.cv_entry.end_date
                else None,
                "detalle": comparison.details,
            }
            for comparison in comparisons
        ]
        args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        logger.info("Resultados guardados en %s", args.output_json)


if __name__ == "__main__":
    main()
