"""Generate the binary fixtures of the offiz_craft browser tests.

Writes, next to this file unless a directory is given:

  sample.docx  the smallest OOXML word-processing package WordCraft opens
               ([Content_Types].xml, _rels/.rels, word/document.xml with one paragraph)
  sample.pdf   a one-page PDF with a line of Helvetica text and a valid xref table
  sample.xlsx  a one-sheet workbook with one inline-str cell (GridCraft opens it)
  sample.pptx  a one-slide presentation with one text shape (DeckCraft opens it)

Both builders are deterministic (fixed ZIP timestamps, no date in the PDF), so running the
script again reproduces the committed bytes and their SHA-256::

    python3 offiz_craft/tests/fixtures/make_fixtures.py [output_dir]

The same files are copied to offiz_craft/static/test/fixtures/, where the standalone host
page (static/test/host.html) fetches them from, at /offiz_craft/static/test/fixtures/<name>.
"""

import argparse
import hashlib
import io
import zipfile
from pathlib import Path

DOCX_PARAGRAPH = "Craft test paragraph."

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" '
    'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    "</Types>"
)

PACKAGE_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="word/document.xml"/>'
    "</Relationships>"
)

DOCUMENT = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    "<w:body>"
    "<w:p><w:r><w:t>" + DOCX_PARAGRAPH + "</w:t></w:r></w:p>"
    "</w:body>"
    "</w:document>"
)


def build_docx() -> bytes:
    """Return a minimal valid .docx (OPC package with a single main document part)."""
    buffer = io.BytesIO()
    # A fixed timestamp keeps the archive byte-for-byte reproducible.
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, xml in (
            ("[Content_Types].xml", CONTENT_TYPES),
            ("_rels/.rels", PACKAGE_RELS),
            ("word/document.xml", DOCUMENT),
        ):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16  # regular file, as Word writes it
            archive.writestr(info, xml.encode("utf-8"))
    return buffer.getvalue()


def build_pdf() -> bytes:
    """Return a one-page PDF 1.4: catalog, page tree, page, Helvetica font, content stream."""
    stream = b"BT\n/F1 24 Tf\n72 770 Td\n(Craft test PDF: one page, Helvetica.) Tj\nET\n"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"endstream",
    ]
    # The second line (a comment with four binary bytes) declares a binary PDF.
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n" % (len(objects) + 1)
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset  # exactly 20 bytes per entry
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        xref,
    )
    return bytes(out)


def _self_check(docx: bytes, pdf: bytes) -> None:
    """Fail loudly if a builder regresses."""
    with zipfile.ZipFile(io.BytesIO(docx)) as archive:
        assert archive.testzip() is None, "docx: corrupt archive"
        assert set(archive.namelist()) == {
            "[Content_Types].xml",
            "_rels/.rels",
            "word/document.xml",
        }, archive.namelist()
    assert pdf.startswith(b"%PDF-1.4\n") and pdf.rstrip().endswith(b"%%EOF"), "pdf: markers"
    startxref = pdf.rindex(b"startxref\n") + len("startxref\n")
    xref = int(pdf[startxref:pdf.index(b"\n", startxref)])
    table = pdf[xref:].split(b"\n")
    assert table[:3] == [b"xref", b"0 6", b"0000000000 65535 f "], table[:3]
    for entry, number in zip(table[3:8], range(1, 6), strict=True):
        offset = int(entry[:10])
        assert pdf[offset:].startswith(b"%d 0 obj" % number), (number, entry)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate the sample.* fixtures.")
    parser.add_argument("output_dir", nargs="?", default=str(Path(__file__).resolve().parent))
    args = parser.parse_args(argv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fixtures = (
        ("sample.docx", build_docx()),
        ("sample.pdf", build_pdf()),
        ("sample.xlsx", build_xlsx()),
        ("sample.pptx", build_pptx()),
    )
    _self_check(fixtures[0][1], fixtures[1][2 - 1])  # the docx and the pdf
    for name, data in fixtures:
        path = output_dir / name
        path.write_bytes(data)
        print(f"{name}: {len(data)} bytes, sha256 {hashlib.sha256(data).hexdigest()}, {path}")
    return 0


def _package(parts):
    """A deterministic OPC zip out of (name, xml) parts."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, xml in parts:
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, xml.encode("utf-8"))
    return buffer.getvalue()


def build_xlsx() -> bytes:
    """A minimal valid .xlsx workbook: one sheet, one inline-str cell (GridCraft opens it)."""
    return _package(
        (
            (
                "[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                "</Types>",
            ),
            (
                "_rels/.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                "</Relationships>",
            ),
            (
                "xl/workbook.xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>',
            ),
            (
                "xl/_rels/workbook.xml.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                "</Relationships>",
            ),
            (
                "xl/worksheets/sheet1.xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Craft test workbook.</t></is></c></row></sheetData>'
                "</worksheet>",
            ),
        )
    )


def build_pptx() -> bytes:
    """A minimal valid .pptx presentation: one slide, one text shape (DeckCraft opens it)."""
    return _package(
        (
            (
                "[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
                '<Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
                "</Types>",
            ),
            (
                "_rels/.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
                "</Relationships>",
            ),
            (
                "ppt/presentation.xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst></p:presentation>',
            ),
            (
                "ppt/_rels/presentation.xml.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>'
                "</Relationships>",
            ),
            (
                "ppt/slides/slide1.xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
                'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>'
                '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title 1"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr/></p:nvSpPr>'
                '<p:spPr><a:xfrm><a:off x="457200" y="457200"/><a:ext cx="8229600" cy="914400"/></a:xfrm>'
                '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
                '<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>Craft test presentation.</a:t></a:r></a:p></p:txBody></p:sp>'
                "</p:spTree></p:cSld></p:sld>",
            ),
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
