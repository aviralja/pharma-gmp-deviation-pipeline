
### * importing * ###
import os
import json
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from src.files.helperfunc import import_data, load_active_prompts, processing_content, process_description
from src.files.agents import llm, summarizerAgent, instructionAnsweringAgent
from src.files.brainstorminghelper import summary_qa
from src.files.vectorstores import MongoVectorStore
from src.files.deviation_store import DeviationSimilarityService
from src.files.redis_repo import DeviationRedisRepository, DeviationUpstashRedisRepository
from dotenv import load_dotenv

load_dotenv()

#! Timer decorator for profiling
def timer(func_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            print(f"⏱️ [{func_name}] took {elapsed:.2f}s")
            return result
        return wrapper
    return decorator


#! Optimized brainstorming function with timing and parallel LLM calls
def brain_optimized(input_data: dict):
    total_start = time.time()
    
    # Step 1: Generate summary (blocking LLM call)
    step_start = time.time()
    summary = summary_qa(input_data['Problem Description and Immediate Action'])
    print(f"⏱️ [1. summary_qa] took {time.time() - step_start:.2f}s")
    
    # Step 2: Load prompts (fast)
    step_start = time.time()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_path = os.path.join(current_dir, "prompts", "Prompts Output 2 1.xlsx")
    prompts = load_active_prompts(prompts_path)
    print(f"⏱️ [2. load_prompts] took {time.time() - step_start:.2f}s")
    
    # Step 3: Process description (blocking LLM call)
    step_start = time.time()
    answer = process_description(summary, llm)
    answers = [answer]
    print(f"⏱️ [3. process_description] took {time.time() - step_start:.2f}s")
    
    # Step 4: Vector similarity search
    step_start = time.time()
    vector_store = MongoVectorStore()
    similarity_service = DeviationSimilarityService(vector_store)
    similar_results = similarity_service.find_similar(answers=answers)
    
    similar_ids = set()
    for result in similar_results:
        hit = result["matches"]
        for sid in hit:
            i = sid.get("metadata", {}).get("summary_id")
            if i:
                similar_ids.add(i)
    
    similarfile = list(similar_ids)
    print(f"⏱️ [4. vector_similarity_search] took {time.time() - step_start:.2f}s - Found {len(similarfile)} similar deviations")
    
    # Step 5: Batch fetch from Redis (OPTIMIZED)
    step_start = time.time()
    redis_repo = DeviationUpstashRedisRepository()
    rootcause_content = "Previous similar root causes for brainstorming:\n"
    
    # Fetch all deviations in batch
    deviation_data = []
    for deviation_id in similarfile:
        data = redis_repo.get_deviation(deviation_id)
        if data:
            deviation_data.append(data)
    
    # Build content string
    for data in deviation_data:
        text = f"""Problem description: {data['problem_description']}\n"
                Root cause: {data['root_cause']}\n
                ########################\n"""
        rootcause_content += text
    
    print(f"⏱️ [5. redis_fetch] took {time.time() - step_start:.2f}s - Fetched {len(deviation_data)} records")
    
    # Step 6: Parallel LLM calls (MAJOR OPTIMIZATION)
    step_start = time.time()
    results = process_prompts_parallel(prompts, summary, rootcause_content)
    print(f"⏱️ [6. parallel_llm_calls] took {time.time() - step_start:.2f}s - Processed {len(prompts)} prompts")
    
    total_time = time.time() - total_start
    print(f"\n🎯 TOTAL TIME: {total_time:.2f}s\n")
    
    return results


#! Process multiple prompts in parallel using ThreadPoolExecutor
def process_prompts_parallel(prompts, summary, rootcause_content):
    QUESTION_KEYS = {
        "Root Cause Brainstorming": "root_cause",
        "Recommended Corrective Action /Preventive Action": "capa",
        "Recommend Corrective Action Effectiveness Check": "capa_effectiveness",
        "Recommend Preventive Action Effectiveness Check": "pa_effectiveness"
    }
    
    results = {}
    
    def process_single_prompt(prompte):
        _, question, prompt = prompte
        question_key = QUESTION_KEYS.get(question, question)
        
        additional_content = ""
        
        # Handle dependencies (note: these may not be available yet in parallel execution)
        if question_key == "root_cause":
            additional_content = rootcause_content
        elif question_key == "capa":
            # This creates a dependency - need to run root_cause first
            additional_content = (
                "The root cause brainstorming is:\n"
                + results.get("root_cause", "")
            )
        elif question_key in ("capa_effectiveness", "pa_effectiveness"):
            # This creates a dependency on capa
            additional_content = (
                "The recommended corrective and preventive actions are:\n"
                + results.get("capa", "")
            )
        
        query = f"""
        You are a gmp expert in pharma industry, your tasked with providing a complete and accurate answer to a user's question by strictly following their specific instructions. content should be in markdown format(compulsory) and strictly as writen

        ---

        **THE ACTUAL QUESTION YOU MUST ANSWER:**
        {question}

        **CONTEXT/KNOWLEDGE BASE TO USE:**
        {summary}

        **HOW TO ANSWER (USER'S INSTRUCTIONS):**
        {prompt}

        {additional_content}

        ---

        ## Question:
        {question}

        ## Answer:
        """
        
        start = time.time()
        output = llm.call(query)
        elapsed = time.time() - start
        print(f"   ↳ LLM call for '{question_key}' took {elapsed:.2f}s")
        
        return question_key, output
    
    # Identify which prompts have dependencies
    independent_prompts = []
    dependent_prompts = []
    
    for prompte in prompts:
        _, question, _ = prompte
        question_key = QUESTION_KEYS.get(question, question)
        
        if question_key == "root_cause":
            independent_prompts.append(prompte)
        elif question_key == "capa":
            dependent_prompts.append(("capa", prompte))
        else:
            dependent_prompts.append(("other", prompte))
    
    # Process independent prompts in parallel first
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_single_prompt, p) for p in independent_prompts]
        for future in futures:
            key, output = future.result()
            results[key] = output
            print(f"   ✓ Completed: {key}")
    
    # Process CAPA (depends on root_cause)
    capa_prompts = [p for dep_type, p in dependent_prompts if dep_type == "capa"]
    if capa_prompts:
        for prompte in capa_prompts:
            key, output = process_single_prompt(prompte)
            results[key] = output
            print(f"   ✓ Completed: {key}")
    
    # Process effectiveness checks (depend on CAPA) in parallel
    other_prompts = [p for dep_type, p in dependent_prompts if dep_type == "other"]
    if other_prompts:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(process_single_prompt, p) for p in other_prompts]
            for future in futures:
                key, output = future.result()
                results[key] = output
                print(f"   ✓ Completed: {key}")
    
    return results


#! Original brainstorming function WITH TIMING
def brain_with_timing(input_data: dict):
    total_start = time.time()
    
    step_start = time.time()
    summary = summary_qa(input_data['Problem Description and Immediate Action'])
    print(f"⏱️ [1. summary_qa] took {time.time() - step_start:.2f}s")
    
    step_start = time.time()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_path = os.path.join(current_dir, "prompts", "Prompts Output 2 1.xlsx")
    prompts = load_active_prompts(prompts_path)
    print(f"⏱️ [2. load_prompts] took {time.time() - step_start:.2f}s")
    
    step_start = time.time()
    answer = process_description(summary, llm)
    answers = [answer]
    print(f"⏱️ [3. process_description] took {time.time() - step_start:.2f}s")
    
    step_start = time.time()
    vector_store = MongoVectorStore()
    similarity_service = DeviationSimilarityService(vector_store)
    similar_results = similarity_service.find_similar(answers=answers)
    
    similar_ids = set()
    for result in similar_results:
        hit = result["matches"]
        for sid in hit:
            i = sid.get("metadata", {}).get("summary_id")
            print(i)
            similar_ids.add(i)
    similarfile = list(similar_ids)
    print(f"⏱️ [4. vector_similarity_search] took {time.time() - step_start:.2f}s")
    
    step_start = time.time()
    redis_repo = DeviationUpstashRedisRepository()
    rootcause_content = "Previous similar root causes for brainstorming:\n"
    for deviation_id in similarfile:
        data = redis_repo.get_deviation(deviation_id)
        if not data:
            continue
        text = f"""Problem description: {data['problem_description']}\n"
                Root cause: {data['root_cause']}\n
                ########################\n"""
        rootcause_content += text
    print(f"⏱️ [5. redis_fetch] took {time.time() - step_start:.2f}s")
    
    results = {}
    QUESTION_KEYS = {
        "Root Cause Brainstorming": "root_cause",
        "Recommended Corrective Action /Preventive Action": "capa",
        "Recommend Corrective Action Effectiveness Check": "capa_effectiveness",
        "Recommend Preventive Action Effectiveness Check": "pa_effectiveness"
    }
    
    step_start = time.time()
    llm_times = []
    for prompte in prompts:
        llm_start = time.time()
        _, question, prompt = prompte
        question_key = QUESTION_KEYS.get(question, question)
        
        additional_content = ""
        if question_key == "root_cause":
            additional_content = rootcause_content
        elif question_key == "capa":
            additional_content = (
                "The root cause brainstorming is:\n"
                + results.get("root_cause", "")
            )
        elif question_key in ("capa_effectiveness", "pa_effectiveness"):
            additional_content = (
                "The recommended corrective and preventive actions are:\n"
                + results.get("capa", "")
            )
        
        query = f"""
        You are a gmp expert in pharma industry, your tasked with providing a complete and accurate answer to a user's question by strictly following their specific instructions. content should be in markdown format(compulsory) and strictly as writen

        ---

        **THE ACTUAL QUESTION YOU MUST ANSWER:**
        {question}

        **CONTEXT/KNOWLEDGE BASE TO USE:**
        {summary}

        **HOW TO ANSWER (USER'S INSTRUCTIONS):**
        {prompt}

        {additional_content}

        ---

        ## Question:
        {question}

        ## Answer:
        """
        
        output = llm.call(query)
        llm_elapsed = time.time() - llm_start
        llm_times.append(llm_elapsed)
        print(f"   ↳ LLM call #{len(llm_times)} for '{question_key}' took {llm_elapsed:.2f}s")
        results[question_key] = output
    
    total_llm_time = time.time() - step_start
    print(f"⏱️ [6. sequential_llm_calls] took {total_llm_time:.2f}s total")
    print(f"   Average per call: {sum(llm_times)/len(llm_times):.2f}s")
    
    total_time = time.time() - total_start
    print(f"\n🎯 TOTAL TIME: {total_time:.2f}s\n")
    
    return results


def save_ans_to_json(ans, filename="brain_output.json"):
    """Save the brain function answers to a JSON file."""
    if not os.path.isabs(filename):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filename = os.path.join(project_root, filename)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(ans, f, indent=2, ensure_ascii=False)
    print(f"Answers saved to {filename}")
