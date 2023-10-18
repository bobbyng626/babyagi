import os
from pydantic import BaseSettings
from typing import NamedTuple

WORK_DIR = os.path.abspath(os.curdir)

class AzureSettings(BaseSettings):
    SEARCH_API_VERSION: str = ''
    SEARCH_ENDPOINT: str = ''
    SEARCH_KEY: str = ''

    OPENAI_API_VERSION_COMPLETION: str = '2022-12-01'
    # OPENAI_API_VERSION_CHAT_COMPLETION: str = "2023-07-01-preview"
    OPENAI_API_VERSION_CHAT_COMPLETION: str = ""
    OPENAI_ENDPOINT: str = ''
    OPENAI_API_KEY: str = ''
    OPENAI_API_TYPE: str = ''

    class Config:
        env_file = f'{WORK_DIR}/config/settings.env'
        env_prefix = 'azure_'
        env_file_encoding = 'utf-8'

# class OpenAISettings(BaseSettings):
#     api_type: str
#     api_version: str
#     api_base: str
#     api_key: str
#     # api_key_2: str

#     class Config:
#         env_file = f'{WORK_DIR}/config/settings.env'
#         env_prefix = 'openai_'
#         env_file_encoding = 'utf-8'


# class SerpApiSettings(BaseSettings):
#     api_key: str

#     class Config:
#         env_file = f'{WORK_DIR}/config/settings.env'
#         env_prefix = 'serpapi_'
#         env_file_encoding = 'utf-8'


class OssSettings(BaseSettings):
    access_key_id: str
    access_key_secret: str

    class Config:
        env_file = f'{WORK_DIR}/config/settings.env'
        env_prefix = 'oss_'
        env_file_encoding = 'utf-8'

class SolaceQueueSettings(BaseSettings):
    RECOMMENDATION_ENGINE_LLM: str = ''
    DECISION_TREE: str = ''
    INVESTMENT_SNAPSHOT: str = ''
    WIN_PLACE_ODDS: str = ''
    ROADMAP: str = ''
    RESULT: str = ''
    WIN_PLACE_CI: str = ''
    POOL_RATIO: str = ''
    EXPECTED_WIN: str = ''
    QUINELLA_WIN_CI: str = ''
    SPEED_PRO: str = ''
    COLD_DOOR: str = ''
    LOSS_DETAIL: str = ''

    class Config:
        env_file = f'{WORK_DIR}/config/settings.env'
        env_prefix = 'solace_queue_'
        env_file_encoding = 'utf-8'


class SolaceTopicSettings(BaseSettings):
    recommendation_engine_llm: str = ''

    class Config:
        env_file = f'{WORK_DIR}/config/settings.env'
        env_prefix = 'solace_topic_'
        env_file_encoding = 'utf-8'


class SolaceSettings(NamedTuple):
    QUEUE: SolaceQueueSettings = SolaceQueueSettings()
    TOPIC: SolaceTopicSettings = SolaceTopicSettings()


class Config(NamedTuple):
    # SERPAPI: SerpApiSettings = SerpApiSettings()
    OSS: OssSettings = OssSettings()
    AZURE: AzureSettings = AzureSettings()
    SOLACE: SolaceSettings = SolaceSettings()


SETTINGS = Config()
