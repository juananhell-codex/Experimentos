from datetime import date

from experience_analyzer.text_parser import parse_experiences_from_text


CERT_TEXT = """
La empresa XYZ S.A. certifica que el señor Juan Pérez se vinculó a partir del 3 de enero de 2020
hasta el 15 de julio de 2021, desempeñando el cargo de analista. Certificado expedido a los 20 días
 del mes de julio de 2021.
"""

CV_TEXT = """
Experiencia Laboral
Entidad: XYZ S.A.
Fecha de ingreso: 03/01/2020
Fecha de retiro: 15/07/2021
"""


def test_parse_certificate_text_extracts_dates():
    records = parse_experiences_from_text(CERT_TEXT, source="Certificado: prueba.pdf")
    assert len(records) == 1
    record = records[0]
    assert record.start_date == date(2020, 1, 3)
    assert record.end_date == date(2021, 7, 15)
    assert record.issue_date == date(2021, 7, 20)
    assert record.effective_end_date == date(2021, 7, 15)
    assert record.experience_days == 560


def test_parse_cv_text_extracts_information():
    records = parse_experiences_from_text(CV_TEXT, source="Hoja de vida: hv.pdf")
    assert len(records) == 1
    record = records[0]
    assert record.start_date == date(2020, 1, 3)
    assert record.end_date == date(2021, 7, 15)
    assert record.experience_days == 560
