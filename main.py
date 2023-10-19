#!/usr/bin/env python3
import os
import time
import logging
from collections import deque
from typing import Dict, List
import importlib
import openai
import chromadb
import tiktoken as tiktoken
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from dotenv import load_dotenv
from settings import SETTINGS
from aexlutils import logger
from agents import TaskAgent, TaskContextAgent, TaskCreationAgent, TaskExecutionAgent, TaskPrioritizationAgent

def init():
    load_dotenv()
    # API Keys
    OPENAI_API_KEY = SETTINGS.AZURE.OPENAI_API_KEY


    # default opt out of chromadb telemetry.
    from chromadb.config import Settings

    client = chromadb.Client(Settings(anonymized_telemetry=False))

    # Engine configuration

    # Model: GPT, LLAMA, HUMAN, etc.
    LLM_MODEL = os.getenv("LLM_MODEL", os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")).lower()

    if not (LLM_MODEL.startswith("llama") or LLM_MODEL.startswith("human")):
        assert OPENAI_API_KEY, "\033[91m\033[1m" + "OPENAI_API_KEY environment variable is missing from .env" + "\033[0m\033[0m"

    # Table config
    RESULTS_STORE_NAME = os.getenv("RESULTS_STORE_NAME", os.getenv("TABLE_NAME", ""))
    assert RESULTS_STORE_NAME, "\033[91m\033[1m" + "RESULTS_STORE_NAME environment variable is missing from .env" + "\033[0m\033[0m"

    # Run configuration
    INSTANCE_NAME = os.getenv("INSTANCE_NAME", os.getenv("BABY_NAME", "BabyAGI"))
    COOPERATIVE_MODE = "none"
    JOIN_EXISTING_OBJECTIVE = False

    # Goal configuration
    OBJECTIVE = os.getenv("OBJECTIVE", "")

    with open("initial_task.txt", 'r') as initial_task_txt:
        # INITIAL_TASK = os.getenv("INITIAL_TASK", os.getenv("FIRST_TASK", ""))
        INITIAL_TASK = initial_task_txt.read()

    # Model configuration
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.0))


    # Extensions support begin

    def can_import(module_name):
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False


    DOTENV_EXTENSIONS = os.getenv("DOTENV_EXTENSIONS", "").split(" ")

    # Command line arguments extension
    # Can override any of the above environment variables
    ENABLE_COMMAND_LINE_ARGS = (
            os.getenv("ENABLE_COMMAND_LINE_ARGS", "false").lower() == "true"
    )
    if ENABLE_COMMAND_LINE_ARGS:
        if can_import("extensions.argparseext"):
            from extensions.argparseext import parse_arguments

            OBJECTIVE, INITIAL_TASK, LLM_MODEL, DOTENV_EXTENSIONS, INSTANCE_NAME, COOPERATIVE_MODE, JOIN_EXISTING_OBJECTIVE = parse_arguments()

    # Human mode extension
    # Gives human input to babyagi
    if LLM_MODEL.startswith("human"):
        if can_import("extensions.human_mode"):
            from extensions.human_mode import user_input_await

    # Load additional environment variables for enabled extensions
    if DOTENV_EXTENSIONS:
        if can_import("extensions.dotenvext"):
            from extensions.dotenvext import load_dotenv_extensions

            load_dotenv_extensions(DOTENV_EXTENSIONS)

    # Extensions support end

    print("\033[95m\033[1m" + "\n*****CONFIGURATION*****\n" + "\033[0m\033[0m")
    print(f"Name  : {INSTANCE_NAME}")
    print(f"Mode  : {'alone' if COOPERATIVE_MODE in ['n', 'none'] else 'local' if COOPERATIVE_MODE in ['l', 'local'] else 'distributed' if COOPERATIVE_MODE in ['d', 'distributed'] else 'undefined'}")
    print(f"LLM   : {LLM_MODEL}")

    # Check if we know what we are doing
    assert OBJECTIVE, "\033[91m\033[1m" + "OBJECTIVE environment variable is missing from .env" + "\033[0m\033[0m"
    assert INITIAL_TASK, "\033[91m\033[1m" + "INITIAL_TASK environment variable is missing from .env" + "\033[0m\033[0m"

    LLAMA_MODEL_PATH = os.getenv("LLAMA_MODEL_PATH", "models/llama-13B/ggml-model.bin")
    if LLM_MODEL.startswith("llama"):
        if can_import("llama_cpp"):
            from llama_cpp import Llama

            print(f"LLAMA : {LLAMA_MODEL_PATH}" + "\n")
            assert os.path.exists(LLAMA_MODEL_PATH), "\033[91m\033[1m" + f"Model can't be found." + "\033[0m\033[0m"

            CTX_MAX = 1024
            LLAMA_THREADS_NUM = int(os.getenv("LLAMA_THREADS_NUM", 8))

            print('Initialize model for evaluation')
            llm = Llama(
                model_path=LLAMA_MODEL_PATH,
                n_ctx=CTX_MAX,
                n_threads=LLAMA_THREADS_NUM,
                n_batch=512,
                use_mlock=False,
            )

            print('\nInitialize model for embedding')
            llm_embed = Llama(
                model_path=LLAMA_MODEL_PATH,
                n_ctx=CTX_MAX,
                n_threads=LLAMA_THREADS_NUM,
                n_batch=512,
                embedding=True,
                use_mlock=False,
            )

            print(
                "\033[91m\033[1m"
                + "\n*****USING LLAMA.CPP. POTENTIALLY SLOW.*****"
                + "\033[0m\033[0m"
            )
        else:
            print(
                "\033[91m\033[1m"
                + "\nLlama LLM requires package llama-cpp. Falling back to GPT-3.5-turbo."
                + "\033[0m\033[0m"
            )
            LLM_MODEL = "gpt-3.5-turbo"

    if LLM_MODEL.startswith("gpt-4"):
        print(
            "\033[91m\033[1m"
            + "\n*****USING GPT-4. POTENTIALLY EXPENSIVE. MONITOR YOUR COSTS*****"
            + "\033[0m\033[0m"
        )

    if LLM_MODEL.startswith("human"):
        print(
            "\033[91m\033[1m"
            + "\n*****USING HUMAN INPUT*****"
            + "\033[0m\033[0m"
        )

    print("\033[94m\033[1m" + "\n*****OBJECTIVE*****\n" + "\033[0m\033[0m")
    print(f"{OBJECTIVE}")

    if not JOIN_EXISTING_OBJECTIVE:
        print("\033[93m\033[1m" + "\nInitial task:" + "\033[0m\033[0m" + f" [To be listed]")
        # print("\033[93m\033[1m" + "\nInitial task:" + "\033[0m\033[0m" + f" {INITIAL_TASK}")
    else:
        print("\033[93m\033[1m" + f"\nJoining to help the objective" + "\033[0m\033[0m")

    # Configure OpenAI
    openai.api_key = SETTINGS.AZURE.OPENAI_API_KEY
    openai.api_type = "azure"
    openai.api_version = "2023-09-15-preview"
    openai.api_base = SETTINGS.AZURE.OPENAI_ENDPOINT

    # Llama embedding function
    class LlamaEmbeddingFunction(EmbeddingFunction):
        def __init__(self):
            return


        def __call__(self, texts: Documents) -> Embeddings:
            embeddings = []
            for t in texts:
                e = llm_embed.embed(t)
                embeddings.append(e)
            return embeddings


    # Results storage using local ChromaDB
    class DefaultResultsStorage:
        def __init__(self):
            logging.getLogger('chromadb').setLevel(logging.ERROR)
            # Create Chroma collection
            chroma_persist_dir = "chroma"
            chroma_client = chromadb.PersistentClient(
                settings=chromadb.config.Settings(
                    persist_directory=chroma_persist_dir,
                )
            )

            metric = "cosine"
            if LLM_MODEL.startswith("llama"):
                embedding_function = LlamaEmbeddingFunction()
            else:
                embedding_function = OpenAIEmbeddingFunction(api_key=OPENAI_API_KEY)
            self.collection = chroma_client.get_or_create_collection(
                name=RESULTS_STORE_NAME,
                metadata={"hnsw:space": metric},
                embedding_function=embedding_function,
            )

        def add(self, task: Dict, result: str, result_id: str):

            # Break the function if LLM_MODEL starts with "human" (case-insensitive)
            if LLM_MODEL.startswith("human"):
                return
            # Continue with the rest of the function

            embeddings = llm_embed.embed(result) if LLM_MODEL.startswith("llama") else None
            if (
                    len(self.collection.get(ids=[result_id], include=[])["ids"]) > 0
            ):  # Check if the result already exists
                self.collection.update(
                    ids=result_id,
                    embeddings=embeddings,
                    documents=result,
                    metadatas={"task": task["task_name"], "result": result},
                )
            else:
                self.collection.add(
                    ids=result_id,
                    embeddings=embeddings,
                    documents=result,
                    metadatas={"task": task["task_name"], "result": result},
                )

        def query(self, query: str, top_results_num: int) -> List[dict]:
            count: int = self.collection.count()
            if count == 0:
                return []
            results = self.collection.query(
                query_texts=query,
                n_results=min(top_results_num, count),
                include=["metadatas"]
            )
            return [item["task"] for item in results["metadatas"][0]]
    


    # Initialize results storage
    def try_weaviate():
        WEAVIATE_URL = os.getenv("WEAVIATE_URL", "")
        WEAVIATE_USE_EMBEDDED = os.getenv("WEAVIATE_USE_EMBEDDED", "False").lower() == "true"
        if (WEAVIATE_URL or WEAVIATE_USE_EMBEDDED) and can_import("extensions.weaviate_storage"):
            WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")
            from extensions.weaviate_storage import WeaviateResultsStorage
            print("\nUsing results storage: " + "\033[93m\033[1m" + "Weaviate" + "\033[0m\033[0m")
            return WeaviateResultsStorage(OPENAI_API_KEY, WEAVIATE_URL, WEAVIATE_API_KEY, WEAVIATE_USE_EMBEDDED, LLM_MODEL, LLAMA_MODEL_PATH, RESULTS_STORE_NAME, OBJECTIVE)
        return None

    def try_pinecone():
        PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
        if PINECONE_API_KEY and can_import("extensions.pinecone_storage"):
            PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
            assert (
                PINECONE_ENVIRONMENT
            ), "\033[91m\033[1m" + "PINECONE_ENVIRONMENT environment variable is missing from .env" + "\033[0m\033[0m"
            from extensions.pinecone_storage import PineconeResultsStorage
            print("\nUsing results storage: " + "\033[93m\033[1m" + "Pinecone" + "\033[0m\033[0m")
            return PineconeResultsStorage(OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_ENVIRONMENT, LLM_MODEL, LLAMA_MODEL_PATH, RESULTS_STORE_NAME, OBJECTIVE)
        return None

    def use_chroma():
        print("\nUsing results storage: " + "\033[93m\033[1m" + "Chroma (Default)" + "\033[0m\033[0m")
        return DefaultResultsStorage()

    results_storage = try_weaviate() or try_pinecone() or use_chroma()

    # Task storage supporting only a single instance of BabyAGI
    class SingleTaskListStorage:
        def __init__(self):
            self.tasks = deque([])
            self.task_id_counter = 0

        def append(self, task: Dict):
            self.tasks.append(task)

        def replace(self, tasks: List[Dict]):
            self.tasks = deque(tasks)

        def popleft(self):
            return self.tasks.popleft()

        def is_empty(self):
            return False if self.tasks else True

        def next_task_id(self):
            self.task_id_counter += 1
            return self.task_id_counter

        def get_task_names(self):
            return [t["task_name"] for t in self.tasks]


    # Initialize tasks storage
    tasks_storage = SingleTaskListStorage()
    if COOPERATIVE_MODE in ['l', 'local']:
        if can_import("extensions.ray_tasks"):
            import sys
            from pathlib import Path

            sys.path.append(str(Path(__file__).resolve().parent))
            from extensions.ray_tasks import CooperativeTaskListStorage

            tasks_storage = CooperativeTaskListStorage(OBJECTIVE)
            print("\nReplacing tasks storage: " + "\033[93m\033[1m" + "Ray" + "\033[0m\033[0m")
    elif COOPERATIVE_MODE in ['d', 'distributed']:
        pass


    # Add the initial task if starting new objective
    if not JOIN_EXISTING_OBJECTIVE:
        
        sample_task_1 = {
            "task_id": tasks_storage.next_task_id(),
            # "task_name": Get actual ranking
            "task_name": "Get the actual ranking for the horse race dated 2023-10-01 race number 1. Give me the ranking in list format."
        }
        sample_task_2 = {
            "task_id": tasks_storage.next_task_id(),
            # "task_name": Predict ranking
            "task_name": "Predict the ranking for the horse race dated 2023-10-01 race number 1 if I want to bet the WIN pool, give me 2 horse reccomendation. Give me the ranking in list format."
        }
        # initial_task = {
        #     "task_id": tasks_storage.next_task_id(),
        #     # "task_name": INITIAL_TASK
        #     "task_name": "Show the steps to " + INITIAL_TASK
        # }
        # tasks_storage.append(sample_task_1)
        tasks_storage.append(sample_task_1) 
        tasks_storage.append(sample_task_2)

    return tasks_storage, results_storage, OBJECTIVE, JOIN_EXISTING_OBJECTIVE


def main():
    tasks_storage, results_storage, OBJECTIVE, JOIN_EXISTING_OBJECTIVE = init()
    os.environ["OPENAI_API_TYPE"] = SETTINGS.AZURE.OPENAI_API_TYPE
    os.environ["OPENAI_API_VERSION"] = SETTINGS.AZURE.OPENAI_API_VERSION_COMPLETION
    # os.environ["OPENAI_API_VERSION"] = SETTINGS.AZURE.OPENAI_API_VERSION_CHAT_COMPLETION
    os.environ["OPENAI_API_BASE"] = SETTINGS.AZURE.OPENAI_ENDPOINT
    os.environ["OPENAI_API_KEY"] = SETTINGS.AZURE.OPENAI_API_KEY
    logger.info("Finished Initialize Parameters")
    loop = True
    while loop:
        # As long as there are tasks in the storage...
        if not tasks_storage.is_empty():
            # Print the task list
            print("\033[95m\033[1m" + "\n*****TASK LIST*****\n" + "\033[0m\033[0m")
            for t in tasks_storage.get_task_names():
                print(" • " + str(t))
            logger.info(f"The Task List: {tasks_storage.tasks}")
            # Step 1: Pull the first incomplete task
            task = tasks_storage.popleft()
            
            print("\033[92m\033[1m" + "\n*****NEXT TASK*****\n" + "\033[0m\033[0m")
            print(str(task["task_name"]))

            context = TaskContextAgent.context_agent(query=OBJECTIVE, top_results_num=5, results_storage=results_storage)
            logger.info(f"The Context: {context}")
            # Send to execution function to complete the task based on the context
            result = TaskExecutionAgent.execution_agent(OBJECTIVE, str(task["task_name"]), context)
            print("\033[93m\033[1m" + "\n*****TASK RESULT*****\n" + "\033[0m\033[0m")
            print(result)

            # Step 2: Enrich result and store in the results storage
            # This is where you should enrich the result if needed
            enriched_result = {
                "data": result
            }
            # extract the actual result from the dictionary
            # since we don't do enrichment currently
            # vector = enriched_result["data"]

            result_id = f"result_{task['task_id']}"

            results_storage.add(task, result, result_id)

            # Step 3: Create new tasks and re-prioritize task list
            # only the main instance in cooperative mode does that

            # ### Create new Tasks
            # new_tasks = TaskCreationAgent.task_creation_agent(
            #     OBJECTIVE,
            #     enriched_result,
            #     task["task_name"],
            #     tasks_storage.get_task_names(),
            # )

            # print('Adding new tasks to task_storage')
            # for new_task in new_tasks:
            #     new_task.update({"task_id": tasks_storage.next_task_id()})
            #     print(str(new_task))
            #     tasks_storage.append(new_task)

            ### Prioritizing with new outcome and actions
            # if not JOIN_EXISTING_OBJECTIVE:
            #     prioritized_tasks = TaskPrioritizationAgent.prioritization_agent(tasks_storage=tasks_storage, objective=OBJECTIVE)
            #     if prioritized_tasks:
            #         tasks_storage.replace(prioritized_tasks)

            # Sleep a bit before checking the task list again
            time.sleep(5)
        else:
            with open("results.txt", "w") as f:
                f.write("No more tasks to complete.\n")
                f.write(results_storage)
                print(results_storage)
            print('Done.')
            loop = False


if __name__ == "__main__":
    main()
