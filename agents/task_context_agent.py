import re
from typing import Dict, List
class TaskContextAgent:
  @classmethod
  # Get the top n completed tasks for the objective
  def context_agent(cls, query: str, top_results_num: int, results_storage):
      """
      Retrieves context for a given query from an index of tasks.

      Args:
          query (str): The query or objective for retrieving context.
          top_results_num (int): The number of top results to retrieve.

      Returns:
          list: A list of tasks as context for the given query, sorted by relevance.

      """
      results = results_storage.query(query=query, top_results_num=top_results_num)
      # print("****RESULTS****")
      # print(results)
      return results
