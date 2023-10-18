from typing import List
import numpy as np
from aexlutils.logger import logger
import bisect

import pandas as pd

from schedule import PastRecordProcessor
from services import PromptGeneratorService


class BANKER_Version5:
    version_num = 5
    past_grouping = {}
    contrast_group_list = []
    use_past_performance = False
    use_top4_record = False
    required_fields = {
        'horse_num': int,
        'win_odds_category': int,
        'is_overbought': bool,
        "win_investment": float,
        "win_odds_diff_group": int,
    }

    @classmethod
    def full_prompt_generator(cls, race_date: str, race_num: int, minute_snapshot: int) -> (str, str):
        df_current_prompt = PromptGeneratorService.get_df_current(race_date, race_num, minute_snapshot)
        # sort win odds and add hot
        df_current_prompt = df_current_prompt.sort_values(by=["win_odds"], ascending=True).head(8).reset_index(drop=True)
        df_current_prompt['hot'] = range(1, len(df_current_prompt) + 1) 
        df_current_prompt["group"] = 1
        # get contrast
        df_contrast = df_current_prompt.groupby(["group"])['win_investment'].agg([
            ("invest_1_over_2", lambda x: (x.nlargest(1)) - (x.nlargest(2).iloc[-1])),
            ("invest_2_over_3", lambda x: (x.nlargest(2).iloc[-1]) - (x.nlargest(3).iloc[-1])),
            ("invest_3_over_4", lambda x: (x.nlargest(3).iloc[-1]) - (x.nlargest(4).iloc[-1]))
        ]).reset_index()
        past_grouping = \
            {'invest_1_over_2': [0, 0.04371879, 0.10360828, 0.19301717, 0.77],
             'invest_2_over_3': [0, 0.01580097, 0.03472222, 0.06296375, 0.43333333],
             'invest_3_over_4': [0, 0.0075, 0.01819232, 0.03568038, 0.17460661]}
        
        # get contrast
        contrast_list = cls.create_contrast_list(df_current_prompt=df_current_prompt,
                                                 df_contrast=df_contrast,
                                                 past_group_dict=past_grouping)
        df_current_prompt["invest_1_over_2_group"] = cls.contrast_group_list[0]

        df_current_prompt['ci_group'] = (df_current_prompt['win_place_ci'] // 0.1).astype(int)
        df_current_prompt['ci_group'] = df_current_prompt['ci_group'].apply(
            lambda x: f"{round(x / 10, 1)}-{round(x / 10 + 0.1, 1)}")
        
        df_expected_ci_jockey = pd.read_csv("jockey_expected_ci.csv")
        df_expected_ci_trainer = pd.read_csv("trainer_expected_ci.csv")
        df_contrast_jockey = pd.read_csv("jockey_contrast.csv")
        df_contrast_trainer = pd.read_csv("trainer_contrast.csv")
        
        # df_expected_ci_jockey, df_expected_ci_trainer = PastRecordProcessor.get_expected_ci_df()
        # df_contrast_jockey, df_contrast_trainer = PastRecordProcessor.get_contrast_df()
        if df_expected_ci_jockey.empty or df_expected_ci_trainer.empty or \
                df_contrast_jockey.empty or df_contrast_trainer.empty:
            logger.error("No expected data")
            return None

        df_current_prompt = df_current_prompt.merge(df_expected_ci_jockey,
                                                    on=["jockey_code", "is_overbought", "ci_group"], how="left")
        df_current_prompt = df_current_prompt.merge(df_expected_ci_trainer,
                                                    on=["trainer_code", "is_overbought", "ci_group"], how="left")
        df_current_prompt = df_current_prompt.merge(df_contrast_jockey,
                                                    on=["jockey_code", "hot", "invest_1_over_2_group"], how="left")
        df_current_prompt = df_current_prompt.merge(df_contrast_trainer,
                                                    on=["trainer_code", "hot", "invest_1_over_2_group"], how="left")
        for col in ["jockey_contrast_win", "jockey_contrast_count", "trainer_contrast_win",
                    "trainer_contrast_count", "jockey_expected_ci_win", "jockey_expected_ci_count",
                    "trainer_expected_ci_win", "trainer_expected_ci_count"]:
            df_current_prompt[col] = df_current_prompt[col].fillna(0)

        df_current_prompt["is_contrast_fail"] = np.where(
            (((df_current_prompt["jockey_contrast_win"] == 0) & (df_current_prompt["jockey_contrast_count"] >= 5))
             | ((df_current_prompt["trainer_contrast_win"] == 0) & (df_current_prompt["trainer_contrast_count"] >= 5))),
            True, ((df_current_prompt["jockey_contrast_win"] + df_current_prompt[
            "trainer_contrast_win"]) / (df_current_prompt["jockey_contrast_count"] + df_current_prompt[
            "trainer_contrast_count"])) < 0.05)

        df_current_prompt["is_expected_ci"] = ((df_current_prompt["jockey_expected_ci_win"] + df_current_prompt[
            "trainer_expected_ci_win"]) / (df_current_prompt["jockey_expected_ci_count"] + df_current_prompt[
            "trainer_expected_ci_count"])) > 0.3

        # Calculate the threshold as 5% of 'win_odds'
        df_current_prompt["win_odds_diff"] = df_current_prompt["expected_win_odds"] - \
                                               df_current_prompt["win_odds"]
        df_current_prompt["win_odds_diff_threshold"] = 0.05 * df_current_prompt['win_odds']
        df_current_prompt['win_odds_diff_group'] = np.where(
            df_current_prompt['win_odds_diff'] > df_current_prompt["win_odds_diff_threshold"], 'More',
            np.where(df_current_prompt['win_odds_diff'] < -df_current_prompt["win_odds_diff_threshold"], 'Less',
                     'Similar'))

        df_current_prompt["win_dd_ratio"] = df_current_prompt["expected_win_odds"] / df_current_prompt[
            "win_odds"]
        df_current_prompt["win_dd_ratio_group"] = df_current_prompt["win_dd_ratio"].apply(
            lambda x: 1 if x <= 0.9 else 2 if x <= 1.1 else 3)
        
        # df_diff_trainer = PastRecordProcessor.get_diff_df()
        df_diff_trainer = pd.read_csv("trainer_dd.csv")
        df_current_prompt = df_current_prompt.merge(df_diff_trainer,
                                                    on=["trainer_code", "win_odds_category",
                                                        "jockey_tier", "win_dd_ratio_group"], how="left")
        df_current_prompt["trainer_dd_percentage_group"] = df_current_prompt["trainer_dd_percentage_group"].fillna(0).apply(
            lambda x: int(x))
        current_race_list = cls.create_current_race(df_current_prompt=df_current_prompt)

        prompt = cls.create_prompt_template(
            current_race=current_race_list,
            contrast_list=contrast_list)
        return prompt

    @classmethod
    def create_current_race(cls, df_current_prompt) -> List[str]:
        current_race_list = ["<Win Odds>\n"]
        for rows in df_current_prompt.itertuples():
            # add record for current race
            current_race_record = f"Horse {rows.horse_num}, " \
                                  f"win odds {rows.win_odds_category}, " \
                                  f"Fail Rate {rows.is_contrast_fail}, " \
                                  f"Expected Investment Change {rows.win_odds_diff_group}, " \
                                  f"OB {rows.is_overbought}, " \
                                  f"Reasonable CI {rows.is_expected_ci}, " \
                                  f"Investment Difference Rate {rows.trainer_dd_percentage_group}, \n" \
                                  f"---\n"
            current_race_list.append(current_race_record)
        return current_race_list

    @classmethod
    def create_contrast_list(cls, df_current_prompt, df_contrast, past_group_dict) -> List[str]:
        contrast_list = ["<Investment Contrast>\n"]
        contrast_group_list = []
        for value in [1, 2, 3]:
            diff_ratio = df_contrast[f'invest_{value}_over_{value + 1}'][0]
            breakpoints = past_group_dict[f'invest_{value}_over_{value + 1}']
            result = ["VERY LOW", "LOW", "HIGH", "VERY HIGH", "VERY HIGH"][
                bisect.bisect_left(breakpoints, diff_ratio) - 1]
            contrast_group_list.append(result)

            contrast_record = f"Contrast of Horse {df_current_prompt['horse_num'][value - 1]} and " \
                              f"Horse {df_current_prompt['horse_num'][value]} " \
                              f"{result}, \n" \
                              f"---\n"
            contrast_list.append(contrast_record)

        cls.contrast_group_list = contrast_group_list
        return contrast_list

    @classmethod
    def create_prompt_template(cls, current_race: List[str], contrast_list: List[str]) -> (str, str):
        current_record = ''.join(current_race)
        contrast_list = ''.join(contrast_list)
        prompt_template = f"""
Act as: You are a horse racing expert at Hong Kong Jockey Club. You will have a race of 4 horses, each horse is ridden by a jockey and trained by a trainer, this forms a horse-jockey-trainer (H-J-T) combination. Your job is to understand all the content in CONCEPTS, distinguish the importance of each CONCEPTS element, then provide recommendation for the user, to see which horse has the most confidence to get into first rank. Important: You MUST use all value in CONCEPTS to judge the winning chance.
Audience: You have to find a horse with highest winning chance, it will be a reference for the candidates to judge a race result.
Format: Follow the ranking, explanation, and description templates shown below to give ranking and explanation. All the data in the context is captured correctly, make sure you read the correct part and capture the correct data for each horse to do analysis. All the data is formed by [CONCEPT] [DATA] format.
Limitation: Based on all the information in this context provide a ranking. Do not search external data and concepts. If you don't know the answer, just say that you don't know. Don't try to make up an answer.
The following prompt will contains these main parts:
"CONCEPTS" is the key idea of this horse racing field, it describe all neccessary concepts to decide the chance of the combination to get into first ranking in the horse race.
"CURRENT RACE" is the user input that includes all current data and insight.
"INSTRUCTION" is the user requirement for the race, it includes some new reminder from user and the final goal of the query, based on the information provided only in this query and CURRENT RACE.
===
CONCEPTS:
0. Ranking is the final ranking of a race with the horse, 1st rank is the best ranking followed by 2nd and 3rd, and so on. For example if a race with 4 horses, the ranking will be like 1st, 2nd, 3rd, 4th. For this 4 horses ranking, 1st means the winner and the first place and 4th means the horse with least winning chance and has worst ranking.
1. I hope you already know the concept of a horse race, with different horse, jockey, trainer and different betting methods with corresponding odds. However, we only focus on "Win" pool now, which is just to find the winner of the race. A horse race is actually a large competition between the participating horses, some horses are strong and have good past result, while some horses are not performing very well or not being trusted by bettors, to win the current race. In the current race, you will have the competitive landscape of these horses, their competitive power is represented by Win Odds value. "Win odds" include 4 values 1/2/3/4, which determine the bettor's confidence level to trust the horse to win the race. Win odds is a very important factor to reflect the actual winning chance of a horse, this has more impact to the final ranking. Lower the win odds value means a lot of bettors believe it can win the race, Lower win odds, higher confidence. Win odds 1 means very high confidence, 2 is relatively high confidence, while 3 is less confidence and 4 show least confidence.
You have the data and sense to determine the winner with win odds, it is normal that you choose the winner with lowest win odds, but only using win odds is not enough to determine the winner.The reason is lower win odds means the profit return is also small, once the winner is not the lowest win odds horse, we will lose all the money and it actually happens a lot. So only by win odds cannot determine the best solution to choose the winner. Also, if the win odds directly deciode the ranking, I would not have to find you for help, so there must be other factors. Now we introduce another measurement, the investment contrast.
"Investment Contrast" means the confidence difference of the horses, by evaluating their invested money from bettor. Some horses does not deserve the high confidence from the bettor, it makes their win odds become very low, we called it overbought, that means the horse takes more confidence and investment than they deserves. We use the investment contrast to compare the investmenr difference of four horses. it includes THREE comparison, contrast of Horse 1 and Horse 2, contrast of Horse 2 and Horse 3, contrast of Horse 3 and Horse 4. each comparison will be represented by "VERY HIGH", "HIGH", "LOW" and "VERY LOW" contrast. VERY HIGH contrast means the former horse has a lot more confidence than the later horse, it also indicates the horse has been overbought and carrying confidence that does not suitable for this horse. VERY LOW contrast means the former horse has slightly or very little contrast only to the later horse only. Use these FOUR contrast ratio to determine the competitive landscape of the horse race. Rank the 4 horses after you evaluate the win odds and the investment contrast.
2. For each H-J-T, another aspect to choose the winner is the "Fail Rate", it indicates a rate for the jockey-trainer combination to win a race under the existing investment contrast situation. If the fail rate is True, it means the J-T (Jocket-Trainer) is too weak and the ranking of the combination will not be good, it has verry low chance to win the horse and you should eliminate the horse or put its ranking backward. Most of the case, if the fail rate is true, the horse is NOT POSSIBLE to win, and you should put it at least after 3rd place. If the fail rate is false, it means the J-T (Jocket-Trainer) is just acting normal.
The following concetps, 3, 4 is the concepts to compare the horse expected behavior and the actual win odds, we use this to evalaute if there are abnormal investment and arrangement on the horse race, to decide if the horse is bought to win or its an hallucination if there are investment.
3. For each H-J-T, we computed an expected invesment for them, indicating the public expectation on the horse to win the race. Then we compare the actual win odds of the horse and the expected investment, to see if the horse now is fulilling a suitable win odds range. There are two values for the "Expected Investement Change", More or Less, More means the horse is getting more investment than expected, Less means the horse is getting less investment from bettors than our expectation.
4. To evlaute the investment intend of the horse, we want to evaluate the win odds of the horse is reasonable or not, so to decide whether we can trust the win odds and use it to judge the winning chance directly, we have 2 aspects, OB (overbought) and Reasonable CI (Confidence interval).
OB means the phenomenon of Overbought, to decide whether the horse is being overly invested, that the investment exceed the capability and strength of the horse. It include 2 values, True or False, where True means the horse is heavily invested and baring way too much confidence and might be failed to win as the win odds is not reflecting the actual strength of the horse. False means the horse is having suitable investment and the win odds reflects a reasonable strength of the horse.
Reasonable CI is another value to judge the confidence of the jockey and trainer is reasonable or not. We have a Confidence Interval (CI) for each combination, but some jockey and trainer is performing better in certain CI range, we describe the combination is reasonable if their CI lies in their comfortable CI range. Reasonable CI True means the horse has reasonable CI and it can perform their best to winner, it shows the intend of the combinaton. False means the horse does not has reasonable CI and might show the win odds of the horse is not trustable
5. Final aspect to judge the winning chance of the horse is the "Investment Difference Rate", under the Expected Investment Change, no matter the horse has more investment or less investment than the expected win odds, there will be a probabilty chance to evaluate the winning chance of the horse. We indicates this winning chance by the "Investment Difference Rate". It contains 4 values, 1/2/3/4, smaller the value means lower winning chance for the combination, higher the value means higher winning chance. Investment Difference Rate 4 means the combination has good past winning chance under the exuisting expected Investment Change, while 1 means the combination has very poor past performance and basically cannot win the race, put the combination in worse rank.
===
CURRENT RACE:
{current_record}
{contrast_list}
===
INSTRUCTION:
Recommend the horse ranking by the chance to win the race with data stated under CURRENT RACE, explain why you choose this horse with explanation and data support.
Give the answer with the following format, replace xxx and yyy by the horse number:
RANKING
1st: Horse xxx, 2nd: Horse yyy, ...
END OF RANKING
===
ANSWER:
"""
        return prompt_template
