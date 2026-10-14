"""Exportacion a Excel (.xlsx) y PDF sin librerias externas (funciona sin internet)."""
import io, zipfile
from xml.sax.saxutils import escape


def _col(i):
    s, i = "", i + 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def xlsx_bytes(titulo, sub, cols, rows):
    def cell(r, i, v, t=None, s=None):
        ref = f"{_col(i)}{r}"
        if isinstance(v, (int, float)) and t != "text":
            return f'<c r="{ref}" s="2"><v>{round(v, 4)}</v></c>'
        st = f' s="{s}"' if s else ""
        return f'<c r="{ref}" t="inlineStr"{st}><is><t>{escape(str(v if v is not None else ""))}</t></is></c>'
    data = [f'<row r="1">{cell(1, 0, titulo, s=1)}</row>', f'<row r="2">{cell(2, 0, sub)}</row>',
            f'<row r="4">{"".join(cell(4, i, c[0], s=1) for i, c in enumerate(cols))}</row>']
    for n, row in enumerate(rows, start=5):
        data.append(f'<row r="{n}">{"".join(cell(n, i, v, cols[i][1]) for i, v in enumerate(row))}</row>')
    widths = "".join(f'<col min="{i+1}" max="{i+1}" width="{max(14, min(45, max([len(str(c[0]))] + [len(str(r[i])) for r in rows[:50]]) + 2))}" customWidth="1"/>'
                     for i, c in enumerate(cols))
    sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
             f'<cols>{widths}</cols><sheetData>{"".join(data)}</sheetData></worksheet>')
    styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
              '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
              '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
              '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
              '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
              '<cellXfs count="3"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
              '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
              '<xf numFmtId="4" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/></cellXfs></styleSheet>')
    files = {
        "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>',
        "_rels/.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        "xl/workbook.xml": '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Reporte" sheetId="1" r:id="rId1"/></sheets></workbook>',
        "xl/_rels/workbook.xml.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>',
        "xl/worksheets/sheet1.xml": sheet, "xl/styles.xml": styles}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for k, v in files.items():
            z.writestr(k, v)
    return buf.getvalue()


def _fmt(v, t):
    if isinstance(v, (int, float)):
        s = f"{v:,.1f}" if t == "pct" else f"{v:,.2f}" if t == "num" else f"{v:,.0f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    return "" if v is None else str(v)


def _pdf_text(s):
    return s.encode("cp1252", "replace").decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def pdf_bytes(titulo, sub, cols, rows):
    W, H, M, FS, LH = 842, 595, 30, 8, 13
    texts = [[_fmt(v, cols[i][1]) for i, v in enumerate(r)] for r in rows]
    lens = [max([len(c[0])] + [len(t[i]) for t in texts]) for i, c in enumerate(cols)]
    lens = [min(max(l, 6), 38) for l in lens]
    scale = (W - 2 * M) / (sum(lens) * FS * 0.52 + 6 * len(cols))
    widths = [(l * FS * 0.52 + 6) * min(scale, 1.6) for l in lens]
    pages, cur, y = [], [], H - M
    def put(x, yy, s, bold=False, size=FS):
        cur.append(f"BT /{'F2' if bold else 'F1'} {size} Tf {x:.1f} {yy:.1f} Td ({_pdf_text(s)}) Tj ET")
    def header():
        nonlocal y
        put(M, y, titulo, True, 14); y -= 16
        put(M, y, sub, False, 8); y -= 20
        x = M
        for i, c in enumerate(cols):
            put(x + 2, y, c[0][:int(widths[i] / (FS * 0.5))], True); x += widths[i]
        cur.append(f"{M} {y - 3:.1f} m {W - M} {y - 3:.1f} l S"); y -= LH
    header()
    for t in texts:
        if y < M + 10:
            pages.append(cur); cur = []; y = H - M; header()
        x, bold = M, str(t[0]).startswith(("TOTAL", "COSTO TOTAL", "=", "Suma"))
        for i, s in enumerate(t):
            maxc = int(widths[i] / (FS * 0.5)); s = s[:maxc]
            tx = x + widths[i] - 3 - len(s) * FS * 0.5 if cols[i][1] != "text" else x + 2
            put(tx, y, s, bold); x += widths[i]
        y -= LH
    pages.append(cur)
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", None,
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"]
    kids = []
    for i, pg in enumerate(pages):
        pg.append(f"BT /F1 7 Tf {W / 2 - 20:.0f} 15 Td (Pagina {i + 1} de {len(pages)}) Tj ET")
        stream = "\n".join(pg)
        objs.append(f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream")
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Contents {len(objs)} 0 R "
                    f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> >>")
        kids.append(f"{len(objs)} 0 R")
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>"
    out = bytearray(b"%PDF-1.4\n"); offs = []
    for n, o in enumerate(objs, 1):
        offs.append(len(out)); out += f"{n} 0 obj\n{o}\nendobj\n".encode("latin-1")
    x = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for o in offs:
        out += f"{o:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF".encode()
    return bytes(out)
