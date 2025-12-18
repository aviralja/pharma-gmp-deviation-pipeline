
### * importing * ###
import os
import json
from files.helperfunc import import_data, load_active_prompts, processing_content,process_description
from files.agents import llm, summarizerAgent, instructionAnsweringAgent
from files.brainstorminghelper import summary_qa
from dotenv import load_dotenv
#! brainstorming function
load_dotenv()
def deviation_generation(input_data: dict):

    prompts=load_active_prompts("../prompts/Prompts Output 1 1.xlsx") 
    print("!")
    summary={}
    for key, value in input_data.items():
        summary[key]=summary_qa(value)
    print("summary done")
    results = {}
    for prompte in prompts:
        section, subsection, prompt = prompte
        query=f"""You are a highly experienced Pharmaceutical GMP document writer and technical editor.

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
        llm_response=llm.call(query)
        results[subsection]=llm_response

        print(f"Completed section: {subsection}")

    return results



def save_ans_to_json(ans, filename="gmp.json"):
    """Save the brain function answers to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(ans, f, indent=2, ensure_ascii=False)
    print(f"Answers saved to {filename}")


if __name__ == "__main__":
    ans = deviation_generation(import_data("question-answer.json"))
    save_ans_to_json(ans)
