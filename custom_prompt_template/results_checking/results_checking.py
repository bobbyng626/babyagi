from typing import List
from aexlutils.logger import logger

class ResultsCheckingTemplate:
  def create_prompt_template(initial_objective: str, accumulated_observation: str) -> str:
    prompt = f"""
      INPUT:
      Your task is to answer user's requirement here: [{initial_objective}]
      You have the following observations by your past answers already: [{accumulated_observation}]
      ---
      You now need to tell me your answer has fulfilled the requirement already or not. 
      If yes, summarize and return a direct answer from your past observation to answer the requirement.
      If the observations have not enough information to answer the requirement, tell me what can be done more.
      ---
      ANSWER:
    """
    return prompt