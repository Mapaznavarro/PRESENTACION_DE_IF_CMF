import csv
import json
import re
import sys
from pathlib import Path

# Requiere: pip install pymupdf
import fitz  # PyMuPDF


TARGET = "REGLAMENTO INTERNO"

def normalize_spaces(s: str) -> str:
    # Normaliza espacios y saltos de línea
    s = s.replace("\u00a0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\r\n|\r", "\n", s)
    return s.strip()

def extract_after_target(text: str, target: str = TARGET) -> str | None:
    """
    Busca el texto inmediatamente después de 'REGLAMENTO INTERNO'.
    Estrategia:
      - busca el target (tolerante a espacios y saltos)
      - toma lo que viene después
      - devuelve la primera "línea/título" razonable (hasta salto de línea),
        limpiando basura típica.
    """
    if not text:
        return None

    # Búsqueda tolerante a whitespace: "REGLAMENTO\s+INTERNO"
    pattern = re.compile(r"REGLAMENTO\s+INTERNO\b", re.IGNORECASE)
    m = pattern.search(text)
    if not m:
        return None

    after = text[m.end():]
    after = after.lstrip(" :\n\t-–—")

    # Tomar primeras líneas y elegir un "título" plausible
    lines = [ln.strip(" \t:-–—") for ln in after.split("\n")]
    lines = [ln for ln in lines if ln]

    if not lines:
        return None

    # Heurística: el nombre suele estar en la primera o segunda línea.
    # Filtramos líneas muy cortas o genéricas.
    blacklist = {
        "FONDO", "REGLAMENTO", "INTERNO", "DE", "LA", "EL", "LOS", "LAS",
        "ADMINISTRADORA", "SOCIEDAD", "FECHA", "VERSION"
    }

    def score(line: str) -> int:
        # Prefiere líneas medianas/largas con letras, evita puro número
        s = 0
        if len(line) >= 8:
            s += 2
        if re.search(r"[A-ZÁÉÍÓÚÑ]", line.upper()):
            s += 2
        if not re.fullmatch(r"[\d\W_]+", line):
            s += 2
        # Penaliza si son solo palabras blacklist
        tokens = re.findall(r"[A-ZÁÉÍÓÚÑ]+", line.upper())
        if tokens and all(t in blacklist for t in tokens):
            s -= 5
        return s

    candidates = lines[:6]  # revisa primeras 6 líneas tras el target
    best = max(candidates, key=score)
    best = re.sub(r"\s{2,}", " ", best).strip()

    # Si aún es muy corto, prueba con la siguiente línea
    if len(best) < 5 and len(lines) > 1:
        best2 = lines[1]
        if len(best2) > len(best):
            best = best2

    return best or None

def extract_text_pymupdf(pdf_path: Path, max_pages: int = 2) -> str:
    """
    Extrae texto de las primeras páginas (por defecto 2),
    suficiente para encontrar el encabezado.
    """
    doc = fitz.open(pdf_path)
    pages = min(len(doc), max_pages)
    chunks = []
    for i in range(pages):
        chunks.append(doc.load_page(i).get_text("text"))
    doc.close()
    return normalize_spaces("\n".join(chunks))

def main():
    if len(sys.argv) < 2:
        print("Uso: python extraer_fondos_swap.py /ruta/a/Fondos_swap")
        sys.exit(2)

    folder = Path(sys.argv[1]).resolve()
    if not folder.exists() or not folder.is_dir():
        print(f"Error: carpeta no existe o no es directorio: {folder}")
        sys.exit(2)

    pdfs = sorted(folder.glob("*.pdf"))
    if not pdfs:
        print(f"No se encontraron PDFs en: {folder}")
        sys.exit(1)

    results = []
    errors = []

    for pdf in pdfs:
        try:
            text = extract_text_pymupdf(pdf, max_pages=2)
            fund = extract_after_target(text, TARGET)
            if not fund:
                errors.append({
                    "archivo": pdf.name,
                    "motivo": f"No se encontró '{TARGET}' o no se pudo extraer el nombre después."
                })
                continue
            results.append({
                "fondo": fund,
                "archivo": pdf.name
            })
        except Exception as e:
            errors.append({
                "archivo": pdf.name,
                "motivo": f"Excepción: {type(e).__name__}: {e}"
            })

    # Salidas
    out_csv = folder / "fondos_swap_fondos.csv"
    out_json = folder / "fondos_swap_fondos.json"
    out_err = folder / "fondos_swap_errores.csv"

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fondo", "archivo"])
        w.writeheader()
        for r in sorted(results, key=lambda x: (x["fondo"].lower(), x["archivo"].lower())):
            w.writerow(r)

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(
            sorted(results, key=lambda x: (x["fondo"].lower(), x["archivo"].lower())),
            f,
            ensure_ascii=False,
            indent=2
        )

    with out_err.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["archivo", "motivo"])
        w.writeheader()
        for e in sorted(errors, key=lambda x: x["archivo"].lower()):
            w.writerow(e)

    print(f"OK: {len(results)} fondos extraídos")
    print(f"Revisar errores: {len(errors)}")
    print(f"CSV:  {out_csv}")
    print(f"JSON: {out_json}")
    print(f"ERR:  {out_err}")

if __name__ == "__main__":
    main()
