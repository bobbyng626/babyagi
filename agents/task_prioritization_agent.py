import re
from typing import Dict, List
from utils import OpenAIQuery

class TaskPrioritizationAgent:
    @classmethod
    def prioritization_agent(cls, tasks_storage, objective: str):
        task_names = tasks_storage.get_task_names()
        bullet_string = '\n'

        prompt = f"""
    You are tasked with prioritizing the following tasks: {bullet_string + bullet_string.join(task_names)}
    Consider the ultimate objective of your team: {objective}.
    Tasks should be sorted from highest to lowest priority, where higher-priority tasks are those that act as pre-requisites or are more essential for meeting the objective.
    Do not remove any tasks. Return the ranked tasks as a numbered list in the format:

    #. First task
    #. Second task

    The entries must be consecutively numbered, starting with 1. The number of each entry must be followed by a period.
    Do not include any headers before your ranked list or follow your list with any other output."""

        # print(f'\n****TASK PRIORITIZATION AGENT PROMPT****\n{prompt}\n')
        print(f'\n****TASK PRIORITIZATION AGENT PROMPT****\n\n')
        response = OpenAIQuery.generate_response(prompt=prompt, max_completion_token=2000)
        # response = openai_call(prompt, max_tokens=2000)
        print(f'\n****TASK PRIORITIZATION AGENT RESPONSE****\n{response}\n')
        if not response:
            print('Received empty response from priotritization agent. Keeping task list unchanged.')
            return
        new_tasks = response.split("\n") if "\n" in response else [response]
        new_tasks_list = []
        for task_string in new_tasks:
            task_parts = task_string.strip().split(".", 1)
            if len(task_parts) == 2:
                task_id = ''.join(s for s in task_parts[0] if s.isnumeric())
                task_name = re.sub(r'[^\w\s_]+', '', task_parts[1]).strip()
                if task_name.strip():
                    new_tasks_list.append({"task_id": task_id, "task_name": task_name})

        return new_tasks_list
