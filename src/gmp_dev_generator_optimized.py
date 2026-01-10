
### * importing * ###
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor
from src.files.helperfunc import import_data, load_active_prompts, processing_content, process_description
from src.files.agents import llm, summarizerAgent, instructionAnsweringAgent
from src.files.brainstorminghelper import summary_qa
from dotenv import load_dotenv

load_dotenv()

#! Optimized deviation generation with timing and parallel processing
def deviation_generation_optimized(input_data: dict):
    total_start = time.time()
    
    # Step 1: Load prompts
    step_start = time.time()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_path = os.path.join(current_dir, "prompts", "Prompts Output 1 1.xlsx")
    prompts = load_active_prompts(prompts_path)
    print(f"⏱️ [1. load_prompts] took {time.time() - step_start:.2f}s - {len(prompts)} prompts")
    
    # Step 2: Generate summaries in PARALLEL (MAJOR OPTIMIZATION)
    step_start = time.time()
    summary = {}
    
    def generate_summary(key_value_pair):
        key, value = key_value_pair
        start = time.time()
        result = summary_qa(value)
        elapsed = time.time() - start
        print(f"   ↳ summary_qa for '{key}' took {elapsed:.2f}s")
        return key, result
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(generate_summary, item) for item in input_data.items()]
        for future in futures:
            key, result = future.result()
            summary[key] = result
    
    print(f"⏱️ [2. parallel_summary_generation] took {time.time() - step_start:.2f}s - {len(summary)} summaries")
    
    # Step 3: Process prompts in PARALLEL (MAJOR OPTIMIZATION)
    step_start = time.time()
    
    def process_single_prompt(prompte):
        section, subsection, prompt = prompte
        
        query = f"""You are a highly experienced Pharmaceutical GMP document writer and technical editor.

        You have strong knowledge of GMP regulations, pharmaceutical quality systems, deviation management, CAPA, root cause analysis, and proper GMP terminology.

        TASK:
        Write the following GMP document section:
        {subsection}

        CONTEXT (PAST KNOWLEDGE):
        {summary[section]}

        INSTRUCTIONS (MUST BE FOLLOWED STRICTLY):
        {prompt}

        REQUIREMENTS:
        - Output must be in **Markdown**
        - Use **professional, regulatory-compliant GMP language**
        - Do **not add or assume facts** beyond the given context
        - Maintain a **formal, audit-ready tone**
        - Use clear headings and bullet points where appropriate
        - Produce only the completed section content

        OUTPUT:
        Return only the written **{subsection}** in Markdown. No explanations or extra text.
        """
        
        start = time.time()
        llm_response = llm.call(query)
        elapsed = time.time() - start
        print(f"   ↳ LLM call for '{subsection}' took {elapsed:.2f}s")
        
        return subsection, llm_response
    
    results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_single_prompt, p) for p in prompts]
        for future in futures:
            subsection, response = future.result()
            results[subsection] = response
            print(f"   ✓ Completed section: {subsection}")
    
    print(f"⏱️ [3. parallel_prompt_processing] took {time.time() - step_start:.2f}s - {len(results)} sections")
    
    total_time = time.time() - total_start
    print(f"\n🎯 TOTAL TIME: {total_time:.2f}s\n")
    
    return results


#! Original with timing instrumentation
def deviation_generation_with_timing(input_data: dict):
    total_start = time.time()
    
    step_start = time.time()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_path = os.path.join(current_dir, "prompts", "Prompts Output 1 1.xlsx")
    prompts = load_active_prompts(prompts_path)
    print(f"⏱️ [1. load_prompts] took {time.time() - step_start:.2f}s")
    
    step_start = time.time()
    summary = {}
    summary_times = []
    for key, value in input_data.items():
        summary_start = time.time()
        summary[key] = summary_qa(value)
        summary_elapsed = time.time() - summary_start
        summary_times.append(summary_elapsed)
        print(f"   ↳ summary_qa #{len(summary_times)} for '{key}' took {summary_elapsed:.2f}s")
    print(f"⏱️ [2. sequential_summary_generation] took {time.time() - step_start:.2f}s total")
    print(f"   Average per summary: {sum(summary_times)/len(summary_times):.2f}s")
    
    step_start = time.time()
    results = {}
    llm_times = []
    for prompte in prompts:
        llm_start = time.time()
        section, subsection, prompt = prompte
        
        query = f"""You are a highly experienced Pharmaceutical GMP document writer and technical editor.

        You have strong knowledge of GMP regulations, pharmaceutical quality systems, deviation management, CAPA, root cause analysis, and proper GMP terminology.

        TASK:
        Write the following GMP document section:
        {subsection}

        CONTEXT (PAST KNOWLEDGE):
        {summary[section]}

        INSTRUCTIONS (MUST BE FOLLOWED STRICTLY):
        {prompt}

        REQUIREMENTS:
        - Output must be in **Markdown**
        - Use **professional, regulatory-compliant GMP language**
        - Do **not add or assume facts** beyond the given context
        - Maintain a **formal, audit-ready tone**
        - Use clear headings and bullet points where appropriate
        - Produce only the completed section content

        OUTPUT:
        Return only the written **{subsection}** in Markdown. No explanations or extra text.
        """
        
        llm_response = llm.call(query)
        results[subsection] = llm_response
        
        llm_elapsed = time.time() - llm_start
        llm_times.append(llm_elapsed)
        print(f"   ↳ LLM call #{len(llm_times)} for '{subsection}' took {llm_elapsed:.2f}s")
    
    print(f"⏱️ [3. sequential_prompt_processing] took {time.time() - step_start:.2f}s total")
    print(f"   Average per call: {sum(llm_times)/len(llm_times):.2f}s")
    
    total_time = time.time() - total_start
    print(f"\n🎯 TOTAL TIME: {total_time:.2f}s\n")
    
    return results


def save_ans_to_json(ans, filename="gmp.json"):
    """Save the brain function answers to a JSON file."""
    if not os.path.isabs(filename):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filename = os.path.join(project_root, filename)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(ans, f, indent=2, ensure_ascii=False)
    print(f"Answers saved to {filename}")
