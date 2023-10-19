
from tools import tools
from langchain.llms import AzureOpenAI
from langchain.prompts import MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent
from langchain.agents import AgentType, AgentExecutor
from aexlutils import logger
class TaskAgent:
  @classmethod
  def task_agent(cls):
    # llm = AzureChatOpenAI(
    #     deployment_name="gpt-35-turbo",
    #     temperature=0
    # )
    llm = AzureOpenAI(
        deployment_name="Test-gpt-35-model",
        temperature=0
    )
    # llm_with_stop = llm.bind(stop=["Observation"])
    chat_history = MessagesPlaceholder(variable_name="chat_history")
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    with open("worker_agent_system_message.txt", "r") as f:
        text = f.read()
    system_message = (text)
    logger.info(system_message)
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        system_message=system_message,
        memory=memory,
        agent_kwargs={
            "memory_prompts": [chat_history],
            "input_variables": ["input", "agent_scratchpad", "chat_history"]
        }
    )
    return agent
