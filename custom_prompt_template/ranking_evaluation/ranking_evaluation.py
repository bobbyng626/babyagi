from typing import List
from aexlutils.logger import logger

class RankingEvaluationTemplate:
  def create_prompt_template(actual_ranking: list, predicted_ranking: list) -> str:
    prompt = f"""
The following problem is related to horse racing analytic in Hong Kong Jockey Club. This prompt serves an evaluation on the predicted ranking and actual ranking of a horse race. You will receive a TWO list, one indicates the actual result of a horse race, which includes 4 horses normally, it means the 4 horses running into first, second, third and forth place; another list indicates the predicted ranking of a horse race, it consists of 4 to 14 horse number in it. Based on the actual result list, evalaute how is the performance of the predicted list. You have the following betting pool to consider:

WIN: Betting correctly for the first ONE rank horse.
QUINELLA: Betting correctly for the first TWO rank horse.
TIERCE: Betting correctly for the first THREE rank horse.
QUARTET: Betting correctly for the first FOUR rank horse.

The rule for betting the pool is simple, we follow a [X in Y] rule to bet. It menas whether first Y horses in predicted ranking are in first X actual ranking. The steps to handle the evaluation is as follow:
1. Extract first X number of horse from actual ranking.
2. Extract first Y number of horse from predicted ranking.
3. Compare and check whether all X horses list are in Y horses list.
4. SUCCESS if Y successfully predicted/included the X result, otherwise FAIL.

EXAMPLE
---
For example we have actual ranking of [1,5,7,2], Horse 1 is winner, Horse 5 is second place, Horse 7 is third place and Horse 2 is forth place. And we have predicted ranking [7,1,8,2,4,5,6,3].
If we bett the WIN pool, we have [1 in 2] betting strategy, which use the first 2 horses in predicted ranking to bet the first ONE rank horse, whether the winner is in this 2 predicted horses. In this case, predicted 2 horses are 7 and 1, and the actual winner is 1 from the actual ranking list, under this [1 in 2] strategy, horse 1 is predicted in first 2 horses and it ran into first place at last, it shows we are SUCCESS in [1 in 2] WIN pool.
REMINDER: the sequence of actual ranking and predicted ranking is not important, if the list include the number already, then they are success.
Similarly, you have to based on the user input of two list to generate a summary on each betting pool and the accuracy on each strategy. Lets output with following format.
[POOL]: [SUCCESS/FAIL] in [Strategy]. Actual[Acutal related Horse] [is/is not] in Predited[Related Predicted horse], [missing if FAIL]
[POOL]: [Strategy]. Actual X is [Actual X horses] Predicted Y is [Predicted Y horses]. Actual [Actual X horses] [is in / is not in] Predicted [Predicted Y horses]; [SUCCESS/FAIL]
===
ONE-SHOT EXAMPLE
---
SAMPLE ACTUAL RANKING: [2,5,4,5]
SAMPLE PREDICTED RANKING: [1,2,3,4,5,6,7]
You have to generate the following pool and strategy:
WIN: [1 in 2], [1 in 3]
QUINELLA: [2 in 4], [2 in 5]
---
WIN: [1 in 2]. Actual X is [2] Predicted Y is [1,2]. [2] is in Predicted[1,2]; SUCCESS
WIN: [1 in 3]. Actual X is [2] Predicted Y is [1,2,3]. [2] is in Predicted[1,2,3]; SUCCESS
QUINELLA: [2 in 4]. Actual X is [2,5] Predicted Y is [1,2,3,4]. [2,5] is not in Predicted[1,2,3,4]; FAIL
QUINELLA: [2 in 5]. Actual X is [2,5] Predicted Y is [1,2,3,4,5]. [2,5] is in Predicted[1,2,3,4,5]; SUCCESS

===
Now you will receive two list for acutal and predicted ranking.
---
Actual ranking: {actual_ranking}
Predicted ranking: {predicted_ranking}
You have to generate the following pool and strategy:
WIN: [1 in 2], [1 in 3]
QUINELLA: [2 in 4], [2 in 5]

ANSWER: 
"""
    return prompt
  

