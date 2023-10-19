# from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
# from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
# import logging
# import os
# import importlib
# # Model: GPT, LLAMA, HUMAN, etc.
# LLM_MODEL = os.getenv("LLM_MODEL", os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")).lower()
# LLAMA_MODEL_PATH = os.getenv("LLAMA_MODEL_PATH", "models/llama-13B/ggml-model.bin")
# # Extensions support begin

# def can_import(module_name):
#     try:
#         importlib.import_module(module_name)
#         return True
#     except ImportError:
#         return False
# if LLM_MODEL.startswith("llama"):
#     if can_import("llama_cpp"):
#         from llama_cpp import Llama

#         print(f"LLAMA : {LLAMA_MODEL_PATH}" + "\n")
#         assert os.path.exists(LLAMA_MODEL_PATH), "\033[91m\033[1m" + f"Model can't be found." + "\033[0m\033[0m"

#         CTX_MAX = 1024
#         LLAMA_THREADS_NUM = int(os.getenv("LLAMA_THREADS_NUM", 8))

#         print('Initialize model for evaluation')
#         llm = Llama(
#             model_path=LLAMA_MODEL_PATH,
#             n_ctx=CTX_MAX,
#             n_threads=LLAMA_THREADS_NUM,
#             n_batch=512,
#             use_mlock=False,
#         )

#         print('\nInitialize model for embedding')
#         llm_embed = Llama(
#             model_path=LLAMA_MODEL_PATH,
#             n_ctx=CTX_MAX,
#             n_threads=LLAMA_THREADS_NUM,
#             n_batch=512,
#             embedding=True,
#             use_mlock=False,
#         )

#         print(
#             "\033[91m\033[1m"
#             + "\n*****USING LLAMA.CPP. POTENTIALLY SLOW.*****"
#             + "\033[0m\033[0m"
#         )
#     else:
#         print(
#             "\033[91m\033[1m"
#             + "\nLlama LLM requires package llama-cpp. Falling back to GPT-3.5-turbo."
#             + "\033[0m\033[0m"
#         )
#         LLM_MODEL = "gpt-3.5-turbo"

# if LLM_MODEL.startswith("gpt-4"):
#     print(
#         "\033[91m\033[1m"
#         + "\n*****USING GPT-4. POTENTIALLY EXPENSIVE. MONITOR YOUR COSTS*****"
#         + "\033[0m\033[0m"
#     )

# if LLM_MODEL.startswith("human"):
#     print(
#         "\033[91m\033[1m"
#         + "\n*****USING HUMAN INPUT*****"
#         + "\033[0m\033[0m"
#     )

# # Llama embedding function
# class LlamaEmbeddingFunction(EmbeddingFunction):
#     def __init__(self):
#         return


#     def __call__(self, texts: Documents) -> Embeddings:
#         embeddings = []
#         for t in texts:
#             e = llm_embed.embed(t)
#             embeddings.append(e)
#         return embeddings

# # Results storage using local ChromaDB
# class DefaultResultsStorage:
#     def __init__(self):
#         logging.getLogger('chromadb').setLevel(logging.ERROR)
#         # Create Chroma collection
#         chroma_persist_dir = "chroma"
#         chroma_client = chromadb.PersistentClient(
#             settings=chromadb.config.Settings(
#                 persist_directory=chroma_persist_dir,
#             )
#         )

#         metric = "cosine"
#         if LLM_MODEL.startswith("llama"):
#             embedding_function = LlamaEmbeddingFunction()
#         else:
#             embedding_function = OpenAIEmbeddingFunction(api_key=OPENAI_API_KEY)
#         self.collection = chroma_client.get_or_create_collection(
#             name=RESULTS_STORE_NAME,
#             metadata={"hnsw:space": metric},
#             embedding_function=embedding_function,
#         )

#     def add(self, task: Dict, result: str, result_id: str):

#         # Break the function if LLM_MODEL starts with "human" (case-insensitive)
#         if LLM_MODEL.startswith("human"):
#             return
#         # Continue with the rest of the function

#         embeddings = llm_embed.embed(result) if LLM_MODEL.startswith("llama") else None
#         if (
#                 len(self.collection.get(ids=[result_id], include=[])["ids"]) > 0
#         ):  # Check if the result already exists
#             self.collection.update(
#                 ids=result_id,
#                 embeddings=embeddings,
#                 documents=result,
#                 metadatas={"task": task["task_name"], "result": result},
#             )
#         else:
#             self.collection.add(
#                 ids=result_id,
#                 embeddings=embeddings,
#                 documents=result,
#                 metadatas={"task": task["task_name"], "result": result},
#             )

#     def query(self, query: str, top_results_num: int) -> List[dict]:
#         count: int = self.collection.count()
#         if count == 0:
#             return []
#         results = self.collection.query(
#             query_texts=query,
#             n_results=min(top_results_num, count),
#             include=["metadatas"]
#         )
#         return [item["task"] for item in results["metadatas"][0]]
