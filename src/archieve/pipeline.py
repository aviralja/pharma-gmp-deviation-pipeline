from typing import Any, Dict, List, Optional, Tuple
import logging

from src.files.CLLM import CustomLLM
from src.files.chroma import (
    setup_chromadb,
    summary_q,
    processing_content,
    store_to_chromadb,
    search_similar_answers,
    similar_deviation,
)


class ChromaStore:
    def __init__(self, logger: logging.Logger):
        self._logger = logger
        self._client, self._collection = setup_chromadb(self._logger)

    @property
    def collection(self):
        return self._collection

    def store_answers(
        self,
        questions_list: List[Dict[str, Any]],
        answers: List[str],
        summary: str,
        summary_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return store_to_chromadb(
            questions_list, answers, summary, self._collection, self._logger, summary_id
        )

    def search(self, query_text: str, top_k: int = 5, print_results: bool = True):
        return search_similar_answers(
            self._collection, query_text, self._logger, n_results=top_k, print_results=print_results
        )


class DeviationRAGPipeline:
    def __init__(
        self,
        llm: CustomLLM,
        logger: logging.Logger,
        chroma_store: Optional[ChromaStore] = None,
    ):
        self._llm = llm
        self._logger = logger
        self._chroma = chroma_store or ChromaStore(logger)

    def summarize_section(self, input_data: Dict[str, Any]) -> str:
        return summary_q(input_data, self._logger, self._llm)

    def answer_questions(
        self, questions_list: List[Dict[str, Any]], summary: str
    ) -> List[str]:
        return processing_content(questions_list, summary, self._logger, self._llm)

    def process_and_store(
        self,
        input_data: Dict[str, Any],
        questions_list: List[Dict[str, Any]],
        summary_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._logger.info("Generating section summary")
        summary = self.summarize_section(input_data)
        self._logger.info("Answering questions")
        answers = self.answer_questions(questions_list, summary)
        self._logger.info("Storing answers to ChromaDB")
        return self._chroma.store_answers(questions_list, answers, summary, summary_id)

    def search(self, query_text: str, top_k: int = 5, print_results: bool = True):
        return self._chroma.search(query_text, top_k=top_k, print_results=print_results)

    def find_similar_deviations(
        self,
        summary_dev: str,
        question_list: List[Dict[str, Any]],
        top_k: int = 3,
    ):
        return similar_deviation(
            summary_dev=summary_dev,
            question_list=question_list,
            collection=self._chroma.collection,
            logging=self._logger,
            llm=self._llm,
            num_results=top_k,
        )


