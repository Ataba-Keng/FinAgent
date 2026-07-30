
"""
Ingestion des documents financiers (PDF) dans le pipeline RAG.

Usage :
    python ingest.py --pdf-dir ./documents

Place tes PDF (rapports annuels, etc.) dans un dossier, ce script :
1. extrait le texte de chaque PDF,
2. le découpe en chunks avec un léger recouvrement,
3. les indexe dans ChromaDB via FinancialRAGPipeline.

Le nom de fichier PDF devient la "source" citée par l'agent, assure-toi donc
qu'il soit lisible (ex: rapport_annuel_2024.pdf, pas document (3).pdf).
"""
import argparse
from pathlib import Path
from typing import List, Tuple

from pypdf import PdfReader

from rag_pipeline import FinancialRAGPipeline

CHUNK_SIZE = 500       # caractères par chunk
CHUNK_OVERLAP = 80     # recouvrement pour ne pas couper une info entre deux chunks


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += size - overlap
    return chunks


def load_pdf_dir(pdf_dir: Path) -> Tuple[List[str], List[str]]:
    all_chunks, all_sources = [], []
    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"Aucun PDF trouvé dans {pdf_dir}")

    for pdf_path in pdf_files:
        text = extract_text(pdf_path)
        if not text.strip():
            print(f"⚠️  Aucun texte extrait de {pdf_path.name} (PDF scanné/image ? OCR nécessaire).")
            continue
        chunks = chunk_text(text)
        all_chunks.extend(chunks)
        all_sources.extend([pdf_path.name] * len(chunks))
        print(f"✅ {pdf_path.name} : {len(chunks)} chunks extraits.")

    return all_chunks, all_sources


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", default="./documents", help="Dossier contenant les PDF à indexer.")
    parser.add_argument("--persist-dir", default="./chroma_store", help="Dossier de persistance ChromaDB.")
    args = parser.parse_args()

    chunks, sources = load_pdf_dir(Path(args.pdf_dir))
    pipeline = FinancialRAGPipeline(persist_dir=args.persist_dir)
    pipeline.index_documents(chunks=chunks, sources=sources)

    print(f"\n{len(chunks)} chunks indexés depuis {len(set(sources))} document(s), "
          f"stockés dans {args.persist_dir}.")