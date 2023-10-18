import bisect
from typing import List


class OddsMapper:
    @classmethod
    def win_odds_grouping(cls, odds: float) -> int:
        if not odds:
            return 999
        breakpoints = [3.5, 8, 18]
        bisect_index = bisect.bisect_left(breakpoints, odds)
        return bisect_index + 1

    @classmethod
    def pool_ratio_grouping(cls, percent: float) -> int:
        if not percent:
            return 999
        if percent > 1.4:
            return 4
        elif percent > 1.25:
            return 3
        elif percent > 1.15:
            return 2
        else:
            return 1

    @classmethod
    def top3_investment_grouping(cls, top3_investment: float) -> int:
        if not top3_investment:
            return "average"
        if top3_investment > 0.6:
            return "high"
        else:
            return "low"

    @classmethod
    def check_tier(cls, jt_code: str, top_tier: List[str], second_tier: List[str]) -> int:
        if not jt_code or not top_tier or not second_tier:
            return 1
        if jt_code in top_tier:
            return 3
        elif jt_code in second_tier:
            return 2
        else:
            return 1

    @classmethod
    def win_tier_percent(cls, percent: float) -> int:
        if not percent:
            return 1
        if percent >= 0.3:
            return 4
        elif percent >= 0.15:
            return 3
        elif percent >= 0.075:
            return 2
        return 1

    @classmethod
    def top4_tier_percent(cls, percent: float) -> int:
        if not percent:
            return 1
        if percent >= 0.6:
            return 4
        elif percent >= 0.4:
            return 3
        elif percent >= 0.2:
            return 2
        return 1

    @classmethod
    def jt_win_tier(cls, first: int, total: int) -> int:
        if total == 0 or not total:
            return 1
        else:
            percent = first / total
            return cls.win_tier_percent(percent)

    @classmethod
    def in_range_score(cls, percent: float) -> int:
        if not percent:
            return 0
        if percent >= 0.3:
            return 4
        elif percent >= 0.2:
            return 3
        elif percent >= 0.1:
            return 2
        else:
            return 1

    @classmethod
    def get_overbought_score(cls, score_dict: dict) -> int:
        if score_dict:
            jockey_percent = score_dict.get("jockey", {}).get("win_percentage", None)
            trainer_percent = score_dict.get("trainer", {}).get("win_percentage", None)
            if None not in [jockey_percent, trainer_percent]:
                if jockey_percent != 0 and trainer_percent != 0:
                    return cls.in_range_score(jockey_percent + trainer_percent)
        return 0

    @classmethod
    def in_wi_score(cls, percent: float) -> int:
        if not percent:
            return 1
        if percent >= 0.3:
            return 4
        elif percent >= 0.2:
            return 3
        elif percent >= 0.1:
            return 2
        else:
            return 1

    @classmethod
    def in_range_score_top4(cls, percent: float) -> int:
        if not percent:
            return 1
        if percent >= 0.6:
            return 4
        elif percent >= 0.4:
            return 3
        elif percent >= 0.2:
            return 2
        else:
            return 1

    @classmethod
    def get_win_investment_true_false(cls, score_dict: dict, minute_snapshot: int) -> int:
        get_minute = minute_snapshot
        if minute_snapshot in [3, 2, 1, 0, -1]:
            get_minute = minute_snapshot + 1
        if score_dict:
            minute_dict = score_dict.get(str(get_minute), None)
            if minute_dict:
                return minute_dict.get("is_invested", False)
        return False

    @classmethod
    def get_win_investment_percent(cls, first: int, total: int) -> float:
        if total == 0 or not total:
            return 0
        else:
            return first / total

    @classmethod
    def get_win_investment_score(cls, score_dict: dict, minute_snapshot: int) -> int:
        get_minute = minute_snapshot
        if minute_snapshot in [3, 2, 1, 0, -1]:
            get_minute = minute_snapshot + 1
        if score_dict:
            minute_dict = score_dict.get(str(get_minute), None)
            if minute_dict:
                jockey_record = minute_dict.get("jockey", [])
                trainer_record = minute_dict.get("trainer", [])
                if None not in [jockey_record, trainer_record]:
                    jockey_percent = cls.get_win_investment_percent(first=jockey_record[0], total=jockey_record[2])
                    trainer_percent = cls.get_win_investment_percent(first=trainer_record[0], total=trainer_record[2])
                    if jockey_percent != 0 and trainer_percent != 0:
                        return cls.in_wi_score(jockey_percent + trainer_percent)
        return 1

    @classmethod
    def get_speed_pro_score(cls, score_dict: dict) -> int:
        if score_dict:
            jockey_percent = score_dict.get("jockeyWinPercent", None)
            trainer_percent = score_dict.get("trainerWinPercent", None)
            if None not in [jockey_percent, trainer_percent]:
                if jockey_percent != 0 and trainer_percent != 0:
                    return cls.in_range_score(jockey_percent + trainer_percent)
        return 0

    @classmethod
    def get_speed_pro_category(cls, speed_pro_diff: int) -> int:
        if speed_pro_diff > 3:
            return 1
        elif speed_pro_diff > 1:
            return 2
        elif speed_pro_diff > -1:
            return 3
        return 4

    @classmethod
    def get_cold_door_score(cls, score_dict: dict) -> int:
        if score_dict:
            jockey_percent = score_dict.get("jockey", {}).get("win_percentage", None)
            trainer_percent = score_dict.get("trainer", {}).get("win_percentage", None)
            if None not in [jockey_percent, trainer_percent]:
                if jockey_percent != 0 and trainer_percent != 0:
                    return cls.in_range_score(jockey_percent + trainer_percent)
        return 0

    @classmethod
    def get_df_score(cls, jockey_percent: float, trainer_percent: float) -> int:
        if None not in [jockey_percent, trainer_percent]:
            if jockey_percent != 0 and trainer_percent != 0:
                return cls.in_range_score(jockey_percent + trainer_percent)
        return 0

    @classmethod
    def get_df_score_top4(cls, jockey_percent: float, trainer_percent: float) -> int:
        if None not in [jockey_percent, trainer_percent]:
            if jockey_percent != 0 and trainer_percent != 0:
                return cls.in_range_score_top4(jockey_percent + trainer_percent)
        return 0

    @classmethod
    def get_df_wi_score(cls, jockey_percent: float, trainer_percent: float) -> int:
        if None not in [jockey_percent, trainer_percent]:
            if jockey_percent != 0 and trainer_percent != 0:
                return cls.in_wi_score(jockey_percent + trainer_percent)
        return 1

    @classmethod
    def get_df_wi_score_top4(cls, jockey_percent: float, trainer_percent: float) -> int:
        if None not in [jockey_percent, trainer_percent]:
            if jockey_percent != 0 and trainer_percent != 0:
                return cls.in_range_score_top4(jockey_percent + trainer_percent)
        return 1

    @classmethod
    def get_bool_reborn_eliminate(cls, horse_num: int, tree_list: list) -> bool:
        if isinstance(tree_list, list):
            for ele in tree_list:
                if ele == horse_num:
                    return True
        return False
