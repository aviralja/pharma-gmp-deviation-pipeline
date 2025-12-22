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
    prompt=f"""You are a GMP deviation analysis assistant.
                Given a detailed deviation problem description, rewrite it into a concise
                2-3 sentence “basic deviation content” that captures ONLY:

                - The fundamental type of problem
                - The process or stage where it occurred
                - The primary root cause category (e.g., supplier issue, human error, equipment, procedure)
                - Why it is considered a deviation from GMP or specifications

                Rules:
                - Do NOT include dates, batch numbers, product names, or company names
                - Do NOT include excessive details or narrative
                - Use neutral, standardized language suitable for similarity comparison
                - Ensure similar root-cause deviations produce very similar outputs

                Deviation Description:
                {summary}
                """
    response=llm.call(prompt)
    response=response if isinstance(response, str) else str(response)
    return response

