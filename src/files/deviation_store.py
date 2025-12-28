from src.files.vectorstores import VectorStore
class DeviationRepository:
    def __init__(self, vector_store: VectorStore):
        self.store = vector_store

    def save_answers(self, summary_id, answers):
        texts, metas, ids = [], [], []

        for i, a in enumerate(answers, 1):
            ids.append(f"{summary_id}_{i}")
            texts.append(a)
            metas.append({
                "summary_id": summary_id,
                "answer":a
            })

        self.store.add(texts, metas, ids)

class DeviationSimilarityService:
    def __init__(self, vector_store: VectorStore):
        self.store = vector_store

    def find_similar(self, answers, top_k=3):
        results = []
        for a in  answers:
            hits = self.store.query(a, top_k)
            results.append({
                "answer": a,
                "matches": hits
            })
        return results
