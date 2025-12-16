import argparse
import json
import logging
import os
from typing import List, Dict, Any

from CLLM import CustomLLM
from helperfunc import import_input_data
from archieve.pipeline import DeviationRAGPipeline


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def build_llm(endpoint: str, model: str, temperature: float) -> CustomLLM:
    return CustomLLM(model=model, endpoint=endpoint, temperature=temperature)


def cmd_process_and_store(args: argparse.Namespace) -> None:
    configure_logging(args.verbose)
    logging.info("Starting process-and-store pipeline")
    
    # Load inputs
    input_data = import_input_data(args.input_json, logging)
    questions_list: List[Dict[str, Any]] = import_input_data(args.questions_json, logging)

    # LLM client
    llm = build_llm(endpoint=args.llm_endpoint, model=args.model, temperature=args.temperature)
    pipeline = DeviationRAGPipeline(llm=llm, logger=logging.getLogger())
    pipeline.process_and_store(input_data, questions_list, summary_id=args.summary_id)


def cmd_search(args: argparse.Namespace) -> None:
    configure_logging(args.verbose)
    llm = build_llm(endpoint=args.llm_endpoint, model=args.model, temperature=args.temperature)
    pipeline = DeviationRAGPipeline(llm=llm, logger=logging.getLogger())
    pipeline.search(args.query, top_k=args.top_k, print_results=True)


def cmd_similar(args: argparse.Namespace) -> None:
    configure_logging(args.verbose)
    questions_list: List[Dict[str, Any]] = import_input_data(args.questions_json, logging)
    llm = build_llm(endpoint=args.llm_endpoint, model=args.model, temperature=args.temperature)
    pipeline = DeviationRAGPipeline(llm=llm, logger=logging.getLogger())
    pipeline.find_similar_deviations(args.summary, questions_list, top_k=args.top_k)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pharma GMP RAG CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    common_llm = argparse.ArgumentParser(add_help=False)
    common_llm.add_argument("--llm-endpoint", default=os.environ.get("LLM_ENDPOINT", "http://127.0.0.1:6969/chat"))
    common_llm.add_argument("--model", default=os.environ.get("LLM_MODEL", "local"))
    common_llm.add_argument("--temperature", type=float, default=float(os.environ.get("LLM_TEMPERATURE", 0)))

    common_flags = argparse.ArgumentParser(add_help=False)
    common_flags.add_argument("-v", "--verbose", action="store_true")

    # process-and-store
    p1 = subparsers.add_parser("process-and-store", parents=[common_llm, common_flags])
    p1.add_argument("--input-json", required=True, help="Path to structured input JSON")
    p1.add_argument("--questions-json", required=True, help="Path to questions JSON")
    p1.add_argument("--summary-id", default=None, help="Optional summary id")
    p1.set_defaults(func=cmd_process_and_store)

    # search
    p2 = subparsers.add_parser("search", parents=[common_llm, common_flags])
    p2.add_argument("--query", required=True, help="Free-text query")
    p2.add_argument("--top-k", type=int, default=5)
    p2.set_defaults(func=cmd_search)

    # similar
    p3 = subparsers.add_parser("similar", parents=[common_llm, common_flags])
    p3.add_argument("--summary", required=True, help="Deviation summary to analyze")
    p3.add_argument("--questions-json", required=True, help="Path to questions JSON")
    p3.add_argument("--top-k", type=int, default=3)
    p3.set_defaults(func=cmd_similar)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()


