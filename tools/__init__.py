from langchain.tools import Tool, StructuredTool

from .ranking_prediction import RankingPredictionTool
from .prompt_selector import PromptSelectorTool
from .prompt_dynamic import DynamicPromptTool
from .ranking_filter import RankingFilterTool
from .ranking_evaluation import RankingEvaluationTool
from .ranking_actual import RankingActualTool
from .race_date import RaceDateTool
from .race_number import RaceNumberTool
from .general import GeneralTool
from .analyze_insight import AnalyzeInsightTool
from .task_list import TaskListTool
from .results_checking import ResultsCheckingTool

tools = [
    PromptSelectorTool(),
    RankingPredictionTool(),
    RankingFilterTool(),
    # DynamicPromptTool(),
    RankingEvaluationTool(),
    RankingActualTool(),
    RaceDateTool(),
    RaceNumberTool(),
    GeneralTool(),
    # TaskListTool(),
    ResultsCheckingTool(),
    # AnalyzeInsightTool()
]
