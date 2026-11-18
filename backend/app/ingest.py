import re, csv, io, json
from typing import List, Dict

# Conservative OCR normalization: repairs common glyph substitutions without
# guessing at arbitrary scientific notation. Every parsed item remains editable.
REPLACEMENTS = {
    '∆': r'\\Delta', 'Δ': r'\\Delta', 'θ': r'\\theta', 'ϑ': r'\\vartheta',
    'ℏ': r'\\hbar', 'ħ': r'\\hbar', '∫': r'\\int', '√': r'\\sqrt',
    '×': r'\\times', '·': r'\\cdot', '→': r'\\rightarrow', '⇌': r'\\rightleftharpoons',
    '≤': r'\\leq', '≥': r'\\geq', '≠': r'\\neq', '±': r'\\pm',
    '°': r'^\\circ', 'μ': r'\\mu', 'λ': r'\\lambda', 'π': r'\\pi',
    'Ω': r'\\Omega', 'ω': r'\\omega', 'α': r'\\alpha', 'β': r'\\beta',
}

def sanitize_text(text: str) -> str:
    text = text.replace('\ufb01', 'fi').replace('\ufb02', 'fl').replace('\u00ad', '')
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\s+([,.;:])', r'\1', text)
    # Keep OCR text intact; only normalize obvious vector notation.
    text = re.sub(r'\bvec\s*\(?([A-Za-z])\)?', r'\\mathbf{\1}', text, flags=re.I)
    return text.strip()

def parse_questions(text: str) -> List[dict]:
    # Heuristic boundaries: numbered lines such as "1." / "1)" / "Q1.".
    matches = list(re.finditer(r'(?m)^\s*(?:Q\s*)?(\d{1,3})\s*[.)]\s+', text))
    out = []
    for i, match in enumerate(matches):
        chunk = text[match.end():matches[i+1].start() if i+1 < len(matches) else len(text)].strip()
        if len(chunk) < 8: continue
        options = []
        opt_matches = list(re.finditer(r'(?m)^\s*\(?([A-D])\)\s*[.)]?\s+', chunk))
        if opt_matches:
            stem = chunk[:opt_matches[0].start()].strip()
            for j, om in enumerate(opt_matches):
                val = chunk[om.end():opt_matches[j+1].start() if j+1 < len(opt_matches) else len(chunk)].strip()
                options.append(f"{om.group(1)}. {sanitize_text(val)}")
        else:
            stem = chunk
        out.append({'number': int(match.group(1)), 'body': sanitize_text(stem), 'options': options, 'answer': None, 'solution': None, 'reviewed': False})
    return out

def parse_answer_csv(raw: bytes) -> Dict[str, str]:
    decoded = raw.decode('utf-8-sig', errors='replace')
    rows = csv.reader(io.StringIO(decoded))
    result = {}
    for row in rows:
        if len(row) >= 2:
            q, a = row[0].strip(), row[1].strip().upper()
            if q.isdigit() and a in {'A','B','C','D','E','1','2','3','4','5'}:
                result[q] = a
    return result
