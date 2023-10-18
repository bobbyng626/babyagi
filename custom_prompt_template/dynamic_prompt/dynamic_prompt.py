from typing import List
from aexlutils.logger import logger

class DynamicPromptTemplate:
  def create_prompt_template(parameter: list) -> str:
    prompt = f"""
      The following problem is related to horse racing analytic in Hong Kong Jockey Club. This prompt serves for creating dynamic prompt for ranking prediction in HKJC horse racing.

      For Example: If you think version "banker_1" is suitable for user, just output "[start/]According to your requirement, you should use version [banker_1] model.[/end]". End the answer after you output the format.
      ---
      JSON LIST:
      {parameter}
      ---
      ANSWER:
    """
    return prompt