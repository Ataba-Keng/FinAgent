import sys
sys.path.append("../agent")
from rag_pipeline import FinancialRAGPipeline

pipeline = FinancialRAGPipeline(persist_dir="../agent/chroma_store")
result = pipeline.collection.get()
sources = set(m["source"] for m in result["metadatas"])
print("--- sources réellement indexées ---")
for s in sources:
    print(repr(s))