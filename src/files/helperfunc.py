import json
from typing import Dict, List, Any
import pandas as pd
import sys


def import_data(filepath: str) -> Dict:
    """Load the structured input data."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            input_data = json.load(f)
            
        return input_data

    except Exception as e:
     
        raise

def load_active_prompts(filepath: str) -> List[List[str]]:
    '''
    Load prompts from an Excel file and return a 2D list of [section, subsection, prompt]
    where 'isactive' is True.
    
    Args:
        filepath (str): Path to the Excel file.
    
    Returns:
        list: A 2D list containing [section, subsection, prompt] for active rows.
    '''
    try:
        # Step 1: Read the Excel file
        df = pd.read_excel(filepath, engine='openpyxl')

        # Step 2: Filter rows where 'isactive is True
        active_rows = df[df['isactive'] == True]

        # Step 3: Extract [section, subsection, prompt] into a 2D list
        prompts = active_rows[['section', 'subsection', 'prompt']].values.tolist()

 
        return prompts

    except Exception as e:
 
        raise

def processing_content(questions_list: List[Dict[str, Any]], summary: str, llm) -> List[str]:
    """
    Process all questions with the given summary and return a list of answers.
    Combines question processing and LLM calls in a single function.
    
    Args:
        questions_list: List of question dictionaries from JSON
        summary: Summary of the deviation to provide context
    
    Returns:
        List of dictionaries containing question and answer
    """
    try:
        expert_template = """You are an expert pharmaceutical GMP deviation analyst with extensive experience in regulatory compliance, quality assurance, and deviation investigation.

    Your task is to analyze the following questions about a GMP deviation and provide a comprehensive, accurate response based on your expertise. Follow the instructions precisely and provide your answer in the format specified.

    Summary of the deviation:
    {summary}
    """
        
        ans: List[str] = []
        total = len(questions_list)
       
        for i, que in enumerate(questions_list, 1):
      
            
            # Format the full prompt with summary and question
            formatted_template = expert_template.format(summary=summary)
            full_prompt = f"{formatted_template}\n\nTask:\n{que['prompt']}"
            
            # Call the LLM
            response = llm.call(full_prompt)
            
            # Append result to the answer list
            ans.append(response if isinstance(response, str) else str(response))            
    
        print("Processing completed for all questions.")
    
        return ans
    except Exception as e:
        raise
def process_description(summary:str,llm) -> List[str]:
    prompt=f"""You are an expert pharmaceutical GMP deviation analyst with strong knowledge of FDA 21 CFR 210/211, EU GMP, ICH Q9, and quality systems.

You are given the following deviation summary:
{summary}

Answer the following 10 questions strictly from a GMP and regulatory perspective. 
Use the format exactly as shown:
# Ans1
# Ans2
...
# Ans10
Do not repeat the questions. Be clear, factual, and inspection-ready.

1. What Went Wrong – In 3–4 sentences, explain what fundamentally went wrong in this deviation, focusing on the type of failure (process, system, equipment, or human) rather than specific minor details.

2. What Failed or Was Bypassed – Describe which control, system, procedure, or barrier was intended to prevent this deviation and explain clearly why it failed or was bypassed.

3. Process and Activity Context – Specify where in the manufacturing or quality process this deviation occurred and what operation or activity was being performed at the time.

4. Why This Matters (Impact and Criticality) – Explain why this deviation is significant from a GMP standpoint, including potential impact on product quality, patient safety, data integrity, or regulatory compliance.

5. Root Cause Indicators – Describe the most likely underlying causes, such as equipment condition, human factors, procedural gaps, training deficiencies, material issues, or system weaknesses.

6. How It Was Detected – Explain how and when the deviation was detected and whether detection occurred as intended by design or incidentally.

7. Historical and Recurrence Context – Indicate whether similar deviations have occurred previously at the site or within the industry and whether this represents a recurring or systemic issue.

8. Scope and Extent – Define how widespread the issue is, including affected batches, products, time period, and whether additional areas or products could potentially be impacted.

9. System and Equipment Involvement – Describe any equipment, systems, automation, environmental, or material factors involved, including their role, condition, and lifecycle status.

10. Technical Keywords and Search Terms – Provide a comma-separated list of relevant technical terms, equipment types, problem types, and GMP terminology that best describe this deviation.
"""
    response=llm.call(prompt)
    response=response if isinstance(response, str) else str(response)
    answers=response.split('#')[1:]
    return answers

