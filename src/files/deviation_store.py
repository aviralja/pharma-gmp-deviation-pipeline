from files.vectorstores import QdrantStore,VectorStore
class DeviationRepository:
    def __init__(self, vector_store: VectorStore):
        self.store = vector_store

    def save_answers(self, summary_id, questions, answers):
        texts, metas, ids = [], [], []

        for i, (q, a) in enumerate(zip(questions, answers), 1):
            ids.append(f"{summary_id}_{i}")
            texts.append(a)
            metas.append({
                "summary_id": summary_id,
                "question": q["question"]
            })

        self.store.add(texts, metas, ids)

class DeviationSimilarityService:
    def __init__(self, vector_store: VectorStore):
        self.store = vector_store

    def find_similar(self, answers, questions, top_k=3):
        results = []
        for q, a in zip(questions, answers):
            hits = self.store.query(a, top_k)
            results.append({
                "question": q,
                "matches": hits
            })
        return results
