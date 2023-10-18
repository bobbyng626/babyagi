from typing import List
from aexlutils.logger import logger

class PromptSelectorTemplate:
  def create_prompt_template(user_requirement: str, prompt_gain_loss_table: list) -> str:
    prompt = f"""
      The following problem is related to horse racing analytic in Hong Kong Jockey Club. You will receive a JSON list list of versions about an AI model and their description, according to user's input, suggest which version the user should use.

      For Example: If you think version "banker_1" is suitable for user, just output "[start/]According to your requirement, you should use version [banker_1] model.[/end]". End the answer after you output the format.
      ---
      JSON LIST:
      {prompt_gain_loss_table}
      ---
      USER REQUIREMENT:
      {user_requirement}
      ---
      ANSWER:
    """
    return prompt