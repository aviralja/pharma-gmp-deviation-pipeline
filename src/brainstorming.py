
### * importing * ###
import os
import json
from files.helperfunc import import_data, load_active_prompts, processing_content,process_description
from files.agents import llm, summarizerAgent, instructionAnsweringAgent
from files.brainstorminghelper import summary_qa
from files.vectorstores import  MongoVectorStore
from files.deviation_store import DeviationSimilarityService
from files.redis_repo import DeviationRedisRepository, DeviationUpstashRedisRepository
from dotenv import load_dotenv
#! brainstorming function
load_dotenv()
def brain(input_data: dict):
    summary=summary_qa(input_data['Problem Description and Immediate Action']) 
    prompts=load_active_prompts("prompts/Prompts Output 2 1.xlsx") 
    answer=process_description(summary,llm)
    answers=[answer]
    vector_store = MongoVectorStore()
    similarity_service = DeviationSimilarityService(vector_store)
    similar_results = similarity_service.find_similar(
                                                    answers=answers
                                                )           
    similar_ids = set()
    for result in similar_results:
        hit = result["matches"]
        for sid in hit:
            i=sid.get("metadata", {}).get("summary_id")
            print(i)
            similar_ids.add(i)
    similarfile = list(similar_ids)
    redis_repo =  DeviationUpstashRedisRepository()
    rootcause_content = "Previous similar root causes for brainstorming:\n"
    for deviation_id in similarfile:
        data = redis_repo.get_deviation(deviation_id)

        if not data:
            continue
        
        text = f"""Problem description: {data['problem_description']}\n"
                Root cause: {data['root_cause']}\n
                ########################\n"""

        
        
        rootcause_content += text        
    results = {}

    QUESTION_KEYS = {
        "Root Cause Brainstorming": "root_cause",
        "Recommended Corrective Action /Preventive Action": "capa",
        "Recommend Corrective Action Effectiveness Check": "capa_effectiveness",
        "Recommend Preventive Action Effectiveness Check": "pa_effectiveness"
    }

    for prompte in prompts:
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

        results[question_key] = output.raw

    return results



def save_ans_to_json(ans, filename="brain_output.json"):
    """Save the brain function answers to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(ans, f, indent=2, ensure_ascii=False)
    print(f"Answers saved to {filename}")


if __name__ == "__main__":
    ans = brain("../reference document/second(complete set)/question-answer2.json")
    save_ans_to_json(ans)

