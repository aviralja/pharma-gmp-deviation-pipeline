import os
from dotenv import load_dotenv
from files.vectorstores import QdrantStore, ChromaStore
from files.deviation_store import DeviationRepository
from files.redis_repo import DeviationRedisRepository
from files.helperfunc import import_data
from files.agents import llm
import uuid
from files.helperfunc import processing_content
load_dotenv()
#! add content to redis and vector store
def add_data(data: dict):
    print("Adding new deviation data...")
    vector_store = ChromaStore(collection_name="deviations")
    print("1")
    dev_store = DeviationRepository(vector_store)
    print("2")
    redis_repo = DeviationRedisRepository(
        host=os.getenv("REDIS_HOST"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0))
    )
    print("3")  
    questions_list=import_data('../information/sepQues.json')
    deviation_id = f"DEV-{uuid.uuid4()}"
    print("$")
    description= data["Description"]
    print("%"  )
    root_cause= data["Root Cause"]
    answers=processing_content(questions_list,description,llm)  
    print("4"   )
    dev_store.save_answers(
        summary_id=deviation_id,
        questions=questions_list,
        answers=answers
    )
    redis_repo.save_deviation(
        deviation_id=deviation_id,
        data={
            "problem_description": description,
            "root_cause": root_cause,
        }
    )
    return deviation_id
