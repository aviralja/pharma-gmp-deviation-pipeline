import os
import hashlib
from typing import List, Dict, Any, Optional
import chromadb


class ChromaDBManager:
    """
    A single-class interface for managing ChromaDB storage, search,
    and deviation similarity analysis without logging or printing.
    """

    def __init__(self, collection_name: str = "pharma_collection", persist_dir: str = "./chromadb_data"):
        self.persist_directory = os.path.abspath(persist_dir)
        os.makedirs(self.persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection_name = collection_name
        self.collection = self._get_or_create_collection(collection_name)

    # ----------------------------
    # Internal helper methods
    # ----------------------------
    def _get_or_create_collection(self, name: str):
        try:
            return self.client.get_collection(name)
        except Exception:
            return self.client.create_collection(name)

    # ----------------------------
    # Store answers + metadata
    # ----------------------------
    def store(
        self,
        questions_list: List[Dict[str, Any]],
        answers: List[str],
        summary: str,
        summary_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Stores answers with metadata in ChromaDB.
        Returns structured information about what was stored.
        """
        if summary_id is None:
            summary_id = f"deviation_{hashlib.md5(summary.encode()).hexdigest()[:8]}"

        document_texts, metadata_list, ids_list = [], [], []

        for i, (que, answer) in enumerate(zip(questions_list, answers), 1):
            doc_id = f"{summary_id}_q{i}"
            document_texts.append(answer)
            metadata_list.append({
                "summary_id": summary_id,
                "summary_text": summary[:200],
                "question_index": i,
                "question": que["question"],
                "question_prompt": que.get("prompt", "")
            })
            ids_list.append(doc_id)

        self.collection.add(
            documents=document_texts,
            metadatas=metadata_list,
            ids=ids_list
        )

        return {
            "summary_id": summary_id,
            "count": len(ids_list),
            "ids": ids_list
        }

    # ----------------------------
    # Search similar answers
    # ----------------------------
    def search_similar(
        self,
        query_text: str,
        n_results: int = 5,
    ) -> Dict[str, Any]:
        """
        Search for similar answers in ChromaDB and return results.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results

    # ----------------------------
    # Similar deviation analysis
    # ----------------------------
    def similar_deviation(
        self,
        summary_dev: str,
        question_list: List[Dict[str, Any]],
        
        answer,
        num_results: int = 3,
    ) -> Dict[str, Any]:
        """
        1. Generate answers using provided LLM + processing_func
        2. Search for top N similar answers
        3. Group results by summary_id
        Returns dict with grouped analysis results.
        """

        # Step 1: Generate answers for deviation
        answers = answer

        # Step 2: Collect all similarity results
        all_results = []
        for i, (que, answer) in enumerate(zip(question_list, answers), 1):
            results = self.collection.query(
                query_texts=[answer],
                n_results=num_results
            )
            for j in range(len(results["ids"][0])):
                all_results.append({
                    "current_question": que["question"],
                    "current_question_index": i,
                    "current_answer": answer,
                    "similar_question": results["metadatas"][0][j]["question"],
                    "similar_question_index": results["metadatas"][0][j]["question_index"],
                    "similar_answer": results["documents"][0][j],
                    "similar_summary_id": results["metadatas"][0][j]["summary_id"],
                    "similar_summary_text": results["metadatas"][0][j]["summary_text"],
                    "similarity_distance": results["distances"][0][j],
                    "document_id": results["ids"][0][j]
                })

        # Step 3: Group results by summary
        grouped_by_summary = {}
        for r in all_results:
            sid = r["similar_summary_id"]
            if sid not in grouped_by_summary:
                grouped_by_summary[sid] = {
                    "summary_text": r["similar_summary_text"],
                    "matched_questions": [],
                    "total_matches": 0,
                    "avg_similarity": 0,
                }

            grouped_by_summary[sid]["matched_questions"].append({
                "current_question": r["current_question"],
                "current_question_index": r["current_question_index"],
                "similar_question": r["similar_question"],
                "similar_question_index": r["similar_question_index"],
                "similarity": r["similarity_distance"]
            })
            grouped_by_summary[sid]["total_matches"] += 1

        # Compute average similarity for each group
        for sid, data in grouped_by_summary.items():
            sims = [m["similarity"] for m in data["matched_questions"]]
            data["avg_similarity"] = sum(sims) / len(sims)

        # Sort summaries by number of matches (descending)
        grouped_by_summary = dict(sorted(
            grouped_by_summary.items(),
            key=lambda x: x[1]["total_matches"],
            reverse=True
        ))

        return {
            "all_results": all_results,
            "grouped_by_summary": grouped_by_summary
        }
