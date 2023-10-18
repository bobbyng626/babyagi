from typing import List, Optional


class LEG_Version9:
    version_num = 9
    use_past_performance = False
    use_top4_record = True
    required_fields = {
        'horse_num': int,
        'win_odds_category': int,
        'jockey_code': str,
        'trainer_code': str,
        'jockey_tier': int,
        'trainer_tier': int,
        'jockey_win_tier': int,
        'trainer_win_tier': int,
        'overbought_score': int,
        'is_invested': bool,
        "investment_snapshot_win_rate": int,
        "speed_pro_score": int,
        "cold_door_score": int,
    }

    @classmethod
    def full_prompt_generator(cls, df_current_prompt, df_past_performance: Optional) -> (str, str):
        current_race_list = cls.create_current_race(df_current_prompt=df_current_prompt)
        horse_num = len(current_race_list)
        prompt = cls.create_prompt_template(
            current_race=current_race_list,
            horse_num=horse_num)
        return prompt

    @classmethod
    def create_current_race(cls, df_current_prompt) -> List[str]:
        current_race_list = []
        for rows in df_current_prompt.itertuples():
            # add record for current race
            current_race_record = f"Horse {rows.horse_num}, win odds {rows.win_odds_category}, " \
                                  f"jockey {rows.jockey_code}, trainer {rows.trainer_code}, " \
                                  f"jockey tier {rows.jockey_tier}, trainer tier {rows.trainer_tier}, " \
                                  f"jockey win rate {rows.jockey_win_tier}, " \
                                  f"trainer win rate {rows.trainer_win_tier}, " \
                                  f"OB {rows.overbought_score}, " \
                                  f"win investment {rows.is_invested}, " \
                                  f"win investment win rate {rows.investment_snapshot_win_rate}, " \
                                  f"Horse Performance {rows.speed_pro_score}, " \
                                  f"JT Performance {rows.cold_door_score}, \n" \
                                  f"---\n"
            current_race_list.append(current_race_record)

        return current_race_list

    @classmethod
    def create_prompt_template(cls, horse_num: int, current_race: List[str]) -> (str, str):
        current_record = ''.join(current_race)
        prompt_template = f"""
SYSTEM:
Act as: You are a horse racing expert at Hong Kong Jockey Club. You will have a race of 7 to 14 horses, each horse is ridden by a jockey and trained by a trainer, this forms a horse-jockey-trainer combination. Your job is to understand all the content in CONCEPTS, analyze the given data and examples, then give rankings to the horse race according to CHAIN OF THOUGHT steps.
Audience: You have to rank a race for each horse and give explanations of each ranking to other horse racing candidates, it will be a reference for the candidates to judge a race result.
Format: Follow the ranking, explanation, and description templates shown below to give ranking and explanation. All the data in the context is captured correctly, make sure you read the correct part and capture the correct data for each horse to do analysis. All the data is formed by [CONCEPT] [DATA] format.
Limitation: Based on all the information in this context provide a ranking. Do not search external data and concepts. If you don't know the answer, just say that you don't know. Don't try to make up an answer.
The following prompt will contains these main parts:
"CONCEPTS" is the key idea of this horse racing field, it describe all neccessary concepts to decide the chance of the combination to get into Top 4 ranking in the horse race.
"CHAIN OF THOUGHT" is the steps to drive down the problem and attempt to give the final ranking, it is the recommended thinking steps that suggested.
"EXAMPLES" is for you to know what will be the sample input abd question from user, in order to understand how to answer the user with the format and the sample content.
CURRENT RACE is the user input that includes all current data and insight, based on these data and the EXAMPLES format and the CHAIN OF THOUGHT steps to rank the horse race with explanation.
===
CONCEPTS:
0. Ranking is the final ranking of a race with the horse, 1st rank is the best ranking followed by 2nd and 3rd, and so on. One important concept in ranking is the "Top 4" ranking, Top 4 means the first four place in the ranking, for example if a race with 7 horses, the ranking will be like 1st, 2nd, 3rd, 4th, 5th, 6th, 7th, Top 4 means the 1st, 2nd, 3rd, 4th rank. For this 7 horses ranking, 1st means the winner and the first place, and 7th means the horse with least winning chance and has worst ranking. If a horse is with win odds 1, it will have highest chance to rank into Top 4 ranking.

1. "Win odds" include 4 values 1/2/3/4, which determine the bettor's confidence level to trust the horse to win the race. Win odds is a very important factor to reflect the actual winning chance of a horse, this has more impact to the final ranking. Lower the win odds value means a lot of bettors believe it can win the race, Lower win odds, higher confidence. Win odds 1 means very high confidence, 2 is relatively high confidence, while 3 and 4 show less confidence. So, for win odds 1 horse, it has a lot of confidence from public so it must be ranked in [1st, 2nd, 3rd, 4th, 5th, 6th, 7th] place no matter how the other data of this horse performs.

2. "Jockey and trainer" information, indicates the strength and performance of jockey and trainer. It includes 2 indexes, Tier and Win Rate.

Jockey and Trainer Tier, includes 3 values 1/2/3, indicates the general strength of the jockey or trainer, tier 3 is the most powerful jockey or trainer and have high confidence, tier 2 is less powerful but still competitive, tier 1 jockey usually has less confidence in Top 4 rank or winner place.

Jockey and Trainer Rate, includes 4 values 1/2/3/4 is interpreted by past race ranking and indicates the jockey or trainer's chance to get into Top 4, separatelyfor jockey and trainer. The jockey or trainer may be favorable to get into top 4 in some specific win odds value. The rate is 4 means the jockey or trainer has a higher chance to get into Top 4, 3 means the jockey or trainer has a medium chance, 2 means the jockey or trainer has a lower chance, and 1 means basically no chance for it.

3. "Investment velocity" indicates the instant confidence change of the horse by the betting amount before the race start. It includes 2 indexes, Overbought and Investment.

Overbought (OB) is the phenomenon of bettors having extreme confidence in the Jockey and Trainer, and betting over the normal level of investment on the jockey trainer for the race. However, some jockey and trainer is not capable to success in an Overbought situation. OB includes 5 values 0/1/2/3/4, OB 0 means the combination does not have the phenomenon of Overbought, meaning bettors normally invest them. OB 1 means the combination has been overbought and has a low chance to get into top 4. Increasing OB means the top 4 chance is also growing, OB 4 means the combination has overbought and has a very high chance to get into Top 4. 

Investment, includes 2 parts, investment and investment rate. investment indicates the combination has an instant increase in confidence or not, True or False. 
investment rate indicates the Top 4 chance of the combination under the investment condition, there can be no increase in confidence, but still, it can get into top 4, or there can be an increase in confidence but the combination cannot be Top 4, it can be reflected by the investment rate 1/2/3/4. 1 means combination has a very low chance to be Top 4 under the current investment level, 4 means a very high confidence level for the combination to get into Top 4 for this investment level.

4. "Past Race Performance" is the performance of the horse-jockey-trainer from past races ranking. It separately describes the general past performance of the horse and jockey-trainer, so we conducted two indexes to evaluate the past performance of these horses and the jockey-trainer combination. These two indexes gives only reference to judge the past race performance of the Jockey-trainer and Horse, their performance might changed due to more training recently, take this as past reference and adjust the ranking rather than directly decide their ranking.

JT Performance Index, which includes 5 values 0/1/2/3/4, indicates the past performance result of the jockey and trainer. JT Performance Index 0 shows a very low occurrence of Top 4 races for this combination while increasing the JT Performance Index means better performance from the past. JT Performance Index 4 means a very high top 4 rank occurrence from past races. Combining the chance for both jockey and trainer by their past performance index and comparing with other jockey and trainer to get the past performance of the combination.

The Horse Performance Index also includes 5 values 0/1/2/3/4, indicating the past performance result of the horses. Horse Performance 0 means the horse has fewer Top 4 rank occurance race before, and 4 means a high number of Top 4 occurance.

5. "Race Distribution" is a race distribution index to tell which horse is likely to get into Top 4 with slightly higher chance based on the win odds. It may contains more than 1 win odds category, this index is interpreted as 1/2/3/4, if the Race distribution is 4, it means there might be higher chance the horse with win odds 4 to get into fronter ranking, if the Race distribution is 1, it means there might be higher chance the horse with win odds 1 to get into fronter ranking. You shall compare the race distribution prediction and the actual ranking is match or not. This attribute add some confidence as reference to those win odds group horse and increase their chance for a little bit to get into Top 4 and winner group. 

6. "Biased Weighting" is the super factor to decide which CONCEPTS is more important than than other. It also describe the brief function and expected influence for each CONCEPTS. Remember, this biased weighting is just a biased, not a deciding factor, so do not influenced significantly by only one factor, other CONCEPTS also has their influence and take them into consideration too. The Biased Weighting will describe the functions of each CONCEPTS and their sequence of ranking, to describe which STEP or CONCEPTS is more important, take more consideration but not all for the higher ranking CONCEPTS. The Biased weighting is an overview to decide which CONCEPTS is more important, it does not count to any CHAIN OF THOUGHT steps but you have to consider it.
===
CHAIN OF THOUGHT:
---
[Step 1]: Consider the Jockey and Trainer for riding the horse, evaluate if this combination is good for getting into Top 4 the race.
---
[Step 2]: Consider the Investment Velocity to see the Bettor's immediate response to the confidence of the horse and some extreme cases of combination
---
[Step 3]: Get the Past Performance of the horse-jockey-trainer, consider as a past race reference for jockey-trainer  and horse strength separately.
--- 
[Step 4]: Use the race distribution to define the context of the race and decide if the horse can get into Top 4 and win the race. Adjust the ranking with it.
---
[Step 5]: Analyze Win Odds for the winning chance of the horse, and compare difference horses win odds to see the current race-winning chance of each horse.
[Reminder] CHAIN OF THOUGHT is just the steps to solve the ranking problem, no factor alone is extremely important to judge the ranking, try to balance each factor and compare the overall horses performance and do the ranking.
===
EXAMPLES:
The following example provides the template and format only, do not directly copy the content, and give all ranking in the final answer with explanation, do not skip Horses.
<SAMPLE CURRENT RACE>
SAMPLE BIASED WEIGHTING:
More Important: Race Distribution, Past Performance, Jockey-Trainer
Less Important: Confidence Contrast, Investment Velocity, Win Matrix
---
Race Distribution favour win odds 2 and 3 horse
---
Horse B678, win odds 2, jockey MMM, trainer BBB, jockey tier 3, trainer tier 3, jockey rate 4, trainer rate 4, OB 3, investment True, investment rate 3, JT Performance 4, Horse Performance 3 
---
Horse C456, win odds 1, jockey EEE, trainer YYY, jockey tier 2, trainer tier 3, jockey rate 3, trainer rate 2, OB 4, investment False, investment rate 1, JT Performance 2, Horse Performance 2 
---
Horse A123, win odds 4, jockey QQQ, trainer WWW, jockey tier 1, trainer tier 3, jockey rate 2, trainer rate 1, OB 0, investment False, investment rate 1, JT Performance 1, Horse Performance 2
<SAMPLE RANKING>
RANKING:
1st: Horse C456, 2nd: Horse B678, 3rd: Horse A123
END OF RANKING
<SAMPLE ANALYSIS ON EXPLANATION>
EXPLANATION:
1st: Horse C456
STEP1 Jockey and Trainer are tier 2 and 3 showing very strong front-tier performance for this combination. Jockey has rate 3 and trainer has rate 2, it shows they have medium to high chance to get into Top 4 rank in the race.
STEP2 For Investment Velocity, it has OB 4, showing there is extreme confidence in this combination and has a very good past winning record, and the combination does not has increase in investment by the investment False, the investment rate here is 1 which shows low investment velocity on the horse and has a relatively low chance to get into Top 4.
STEP3 Consider the past race performance, the JT Performance had a medium Top 4 rank occurrence in past races as the index is 2, and the Horse performance is 2 also indicates a medium record for the horse, it shows a medium performance on past records.
STEP4 The race distribution also favor this horse as it is Win odds 2, it has more chance to get into Top 4 and win the race.
STEP5 For the win odds, it has win odds 1, it has a lot of confidence and is trusted by public that can win, indicating it has a relatively high investment in the win, with very high chance to win the race, I must put it into Top 4 ranking, so its rank will always in [1st, 2nd, 3rd, 4th]
---
2nd: Horse B678
STEP1 Jockey and Trainer are tier 3 and 3 showing very strong front-tier performance for this combination. They both have a rate of 4 showing a very good and high top 4 rate in this race.
STEP2 For Investment Velocity, it has OB 3, showing there is extreme confidence in this combination and has a quite good past Top 4 record, and the combination has more instant increase in investment by the investment true, the investment rate here is 3 which shows high investment velocity on the horse and has a relatively high Top 4 chance. It might have more confidence in the current race.
STEP3 Consider the past race performance, the JT Performance had a very high Top 4 occurrence in past races as the index is 4, and the Horse performance is 3 indicating a quite good record for the horse, it shows a good performance on past records.
STEP4 The race distribution also favor this horse as it is Win odds 2, it has more chance to get into Top 4 and win the race.
STEP5 For the win odds, it has win odds 2, indicating it has a relatively high investment in the win, with quite high chance to win the race.
---
<Similar explanation for Horse A123>
END OF EXPLANATION
===
CURRENT RACE:
BIASED WEIGHTING:
More Important: Win Odds, Race Distribution, Past Performance, Investment Velocity, Jockey-Trainer
---
Less Important: NONE
---
Race Distribution favour win odds 1 horse
---
{current_record}
===
QUESTION:
Remember Horse A123 and B678 and C456 are sample horses, DO NOT include them in RANKING or EXPLANATION
What will be the ranking of the horses and explain the reason in detail?
Rank all horses stated under CURRENT RACE, there should be {horse_num} horses in total, after giving the list, explain the reason according to your predicted ranking from CHAIN OF THOUGHT. Give the ranking in the following format, follow the content format shown in the EXAMPLE:
RANKING... END OF RANKING
EXPLANATION... EXPLANATION
===
ANSWER:
"""
        return prompt_template
