class RankingFilterTemplate:
  def create_prompt_template(user_requirement: str, predicted_ranking_full: list) -> str:
    prompt = f"""
You are going to receive a ranking list about horse racing rank, each number represent the horser number in the horse race. Starting from best horse to worst horse. According to user requirment, you have to filter the required quantity of horses and return the horse number ranking.

User may give you directly the pool name: you have to understand the meanings too.
WIN: Betting correctly for the first ONE rank horse, you can suggest the first 2 horses to the user to choose.
QUINELLA: Betting correctly for the first TWO rank horse, you can suggest the first 4 horses to the user to choose.
TIERCE: Betting correctly for the first THREE rank horse, you can suggest the first 6 horses to the user to choose.
QUARTET: Betting correctly for the first FOUR rank horse, you can suggest the first 7 horses to the user to choose.

For Example: You receive the ranking like [1,4,5,7,2,9,8,6,3], if user required Top 4 rank horse. Then, you have to return [1,4,5,7] as the Top 4 rank.
---
HORSE LIST:
{predicted_ranking_full}
---
USER REQUIREMENT:
{user_requirement}
---
ANSWER:
    """
    return prompt