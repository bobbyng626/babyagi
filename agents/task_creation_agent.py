import re
from typing import Dict, List
from utils import OpenAIQuery

class TaskCreationAgent:
  @classmethod
  def task_creation_agent(
          cls, objective: str, result: Dict, task_description: str, task_list: List[str]
  ):
      prompt = f"""
  You are to use the result from an execution agent to create new tasks with the following objective: {objective}.
  The last completed task has the result: \n{result["data"]}
  This result was based on this task description: {task_description}.\n"""

      if task_list:
          prompt += f"These are incomplete tasks: {', '.join(task_list)}\n"
      prompt += "Based on the result, return a list of tasks to be completed in order to meet the objective. "
      if task_list:
          prompt += "These new tasks must not overlap with incomplete tasks. "

      prompt += """
  Return one task per line in your response. The result must be a numbered list in the format:

  #. First task
  #. Second task

  The number of each entry must be followed by a period. If your list is empty, write "There are no tasks to add at this time."
  Unless your list is empty, do not include any headers before your numbered list or follow your numbered list with any other output."""

      print(f'\n*****TASK CREATION AGENT PROMPT****\n{prompt}\n')
      response = OpenAIQuery.generate_response(prompt=prompt, max_completion_token=2000)
      print(f'\n****TASK CREATION AGENT RESPONSE****\n{response}\n')
      new_tasks = response.split('\n')
      new_tasks_list = []
      for task_string in new_tasks:
          task_parts = task_string.strip().split(".", 1)
          if len(task_parts) == 2:
              task_id = ''.join(s for s in task_parts[0] if s.isnumeric())
              task_name = re.sub(r'[^\w\s_]+', '', task_parts[1]).strip()
              if task_name.strip() and task_id.isnumeric():
                  new_tasks_list.append(task_name)
              # print('New task created: ' + task_name)

      out = [{"task_name": task_name} for task_name in new_tasks_list]
      return out
