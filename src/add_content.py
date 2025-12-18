import os
from dotenv import load_dotenv
from files.vectorstores import QdrantStore, ChromaStore, MongoVectorStore
from files.deviation_store import DeviationRepository
from files.redis_repo import DeviationRedisRepository, DeviationUpstashRedisRepository
from files.helperfunc import import_data
from files.agents import llm
import uuid
from files.helperfunc import process_description
load_dotenv()
#! add content to redis and vector store
def add_data(data: dict):
    print("Adding new deviation data...")
    vector_store = MongoVectorStore()
    print("1")
    dev_store = DeviationRepository(vector_store)
    print("2")
    redis_repo = DeviationUpstashRedisRepository()
    print("3")  
    # questions_list=import_data('../information/sepQues.json') #!reducing time
    deviation_id = f"DEV-{uuid.uuid4()}"
    print("$")
    description= data["Description"]
    print("%"  )
    root_cause= data["Root Cause"]
    answers=process_description(description,llm)  
    print("4")
    dev_store.save_answers(deviation_id, answers)
    redis_repo.save_deviation(
        deviation_id=deviation_id,
        data={
            "problem_description": description,
            "root_cause": root_cause,
        }
    )
    return deviation_id
