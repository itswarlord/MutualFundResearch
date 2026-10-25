"""
excel_writer.py - Zero-dependency, pure-Python OpenXML (.xlsx) multi-sheet workbook generator.
Compliant with Microsoft Excel, LibreOffice, Google Sheets, and Apple Numbers.
"""

import zipfile
import xml.sax.saxutils
from typing import Dict, List, Any


def write_xlsx(filename: str, sheets: Dict[str, List[List[Any]]]):
    """
    Creates an OpenXML (.xlsx) file with multiple sheets.
    sheets format: {
        "Sheet Name": [
            ["Col1", "Col2", ...],  # Header row
            [val1, val2, ...],      # Data row 1
            ...
        ]
    }
    """
    sheet_names = list(sheets.keys())
    if not sheet_names:
        raise ValueError("Cannot write empty workbook with zero sheets")

    # Sanitize sheet names: max 31 chars, no special characters
    def clean_sheet_name(name: str) -> str:
        invalid_chars = set("[]:*?/\\")
        cleaned = "".join(c for c in name if c not in invalid_chars)[:31].strip()
        return cleaned or "Sheet"

    sanitized_sheets = {}
    used_names = set()
    for name, rows in sheets.items():
        s_name = clean_sheet_name(name)
        orig_s_name = s_name
        counter = 1
        while s_name in used_names:
            s_name = f"{orig_s_name[:28]}_{counter}"
            counter += 1
        used_names.add(s_name)
        sanitized_sheets[s_name] = rows

    num_sheets = len(sanitized_sheets)

    with zipfile.ZipFile(filename, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. [Content_Types].xml
        sheet_types = "".join([
            f'<Override PartName="/xl/worksheets/sheet{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for i in range(num_sheets)
        ])
        zf.writestr("[Content_Types].xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  {sheet_types}
</Types>""")

        # 2. _rels/.rels
        zf.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""")

        # 3. xl/_rels/workbook.xml.rels
        sheet_rels = "".join([
            f'<Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i+1}.xml"/>'
            for i in range(num_sheets)
        ])
        zf.writestr("xl/_rels/workbook.xml.rels", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  {sheet_rels}
</Relationships>""")

        # 4. xl/workbook.xml
        sheets_xml = "".join([
            f'<sheet name="{xml.sax.saxutils.escape(name)}" sheetId="{i+1}" r:id="rId{i+1}"/>'
            for i, name in enumerate(sanitized_sheets.keys())
        ])
        zf.writestr("xl/workbook.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>{sheets_xml}</sheets>
</workbook>""")

        # 5. Write each worksheet
        for idx, (sheet_name, rows) in enumerate(sanitized_sheets.items(), 1):
            rows_xml = []
            for r_idx, row in enumerate(rows, 1):
                cells_xml = []
                for c_idx, val in enumerate(row, 1):
                    # Calculate column letter (e.g. 1 -> A, 27 -> AA)
                    col_letter = ""
                    temp = c_idx
                    while temp > 0:
                        temp, rem = divmod(temp - 1, 26)
                        col_letter = chr(65 + rem) + col_letter
                    ref = f"{col_letter}{r_idx}"

                    if val is None or val == "":
                        continue
                    elif isinstance(val, (int, float)):
                        cells_xml.append(f'<c r="{ref}" t="n"><v>{val}</v></c>')
                    else:
                        esc = xml.sax.saxutils.escape(str(val))
                        cells_xml.append(f'<c r="{ref}" t="inlineStr"><is><t>{esc}</t></is></c>')
                rows_xml.append(f'<row r="{r_idx}">{" ".join(cells_xml)}</row>')

            zf.writestr(f"xl/worksheets/sheet{idx}.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>{" ".join(rows_xml)}</sheetData>
</worksheet>""")
