from memory_storage import MemoryStorage
from schedule import PastRecordProcessor
from schema import MemoryKeyPrefix
import pandas as pd
from aexlutils.logger import logger
from utils import OddsMapper

pd.set_option('display.max_columns', None)


class PromptGeneratorService:
    @classmethod
    def fetch_from_redis_to_df(cls, race_date: str, race_num: int, minute_snapshot: int) -> pd.DataFrame:
        logger.info(f"Getting redis data on {race_date} {race_num} {minute_snapshot}")
        df_race_card = cls.get_race_card(race_date, race_num)
        df_road_map = cls.get_roadmap(race_date, race_num)
        df_win_place = cls.get_win_place(race_date, race_num)
        df_quinella_win_ci = cls.get_quinella_win_ci(race_date, race_num)
        df_speed_pro = cls.get_speed_pro(race_date, race_num)
        df_cold_door = cls.get_cold_door(race_date, race_num)
        df_investment_snapshot = cls.get_investment_snapshot(race_date, race_num, minute_snapshot)
        df_ob = cls.get_overbought_from_win_place_ci(race_date, race_num)
        df_expected_win = cls.get_expected_odds(race_date, race_num)
        # df_loss_detail = cls.get_loss_detail(race_date, race_num)
        if df_race_card.empty or df_win_place.empty or df_road_map.empty or df_ob.empty:
            logger.error(f"Failed to get prompt data from redis")
            return pd.DataFrame()

        df_final = df_race_card.merge(
            df_road_map, on="horse_num", how="left")
        df_final = df_final.merge(
            df_win_place, on="horse_num", how="left")
        df_final = df_final.merge(
            df_investment_snapshot, on="horse_num", how="left").fillna(0)
        df_final = df_final.merge(
            df_ob, on="horse_num", how="left")
        df_final = df_final.merge(
            df_expected_win, on="horse_num", how="left").fillna(0)
        df_final = df_final.merge(
            df_quinella_win_ci, on="horse_num", how="left").fillna(0)
        df_final = df_final.merge(
            df_speed_pro, on="horse_num", how="left").fillna(0)
        df_final = df_final.merge(
            df_cold_door, on="horse_num", how="left").fillna(0)
        top_6_jockeys = PastRecordProcessor.top_6_jockeys
        second_6_jockeys = PastRecordProcessor.second_6_jockeys
        top_6_trainers = PastRecordProcessor.top_6_trainers
        second_6_trainers = PastRecordProcessor.second_6_trainers
        for jt_list in [top_6_jockeys, second_6_jockeys, top_6_trainers, second_6_trainers]:
            if not jt_list:
                logger.error(f"Failed to get top 6 jockeys or trainers")
                return pd.DataFrame()

        df_final["jockey_tier"] = df_final["jockey_code"].apply(lambda x: OddsMapper.check_tier(
            x, top_6_jockeys, second_6_jockeys))
        df_final["trainer_tier"] = df_final["trainer_code"].apply(lambda x: OddsMapper.check_tier(
            x, top_6_trainers, second_6_jockeys))

        return df_final
    
    @classmethod
    def get_df_current(cls, race_date: str, race_num: int, minute_snapshot: int):
        df_current = cls.fetch_from_redis_to_df(race_date, race_num, minute_snapshot)
        if df_current.empty:
            logger.error(f"Failed to get current prompt list")
            return None
        return df_current

    @classmethod
    def get_df_loss_detail(cls, race_date: str, race_num: int, minute_snapshot: int):
        df_loss_detail = cls.get_loss_detail(race_date, race_num)
        if df_loss_detail.empty:
            logger.error(f"Failed to get loss detail")
        return df_loss_detail
    
    @classmethod
    def get_race_card(cls, race_date: str, race_num: int) -> pd.DataFrame:
        race_card_horse_list = MemoryStorage.fetch_by_key(
            MemoryKeyPrefix.RACE_CARD_RECORD,
            race_date, race_num, "horses")
        if not race_card_horse_list:
            logger.error(f"Failed to get race card score")
            return pd.DataFrame()
        extracted_data = [
            {
                "horse_num": str(d["horse_num"]),
                "horse_code": d["horse_code"],
                "jockey_code": d["jockey_code"],
                "trainer_code": d["trainer_code"],
                "scratched": d["scratched"]
            }
            for d in race_card_horse_list
        ]
        df = pd.DataFrame(extracted_data)
        df = df[df["scratched"] == False]
        logger.info(f"Succesfully fetch from Redis")
        return df

    @classmethod
    def get_roadmap(cls, race_date: str, race_num: int) -> pd.DataFrame:
        required_fields = ["horse_num", "cold_door", "overbought_statistics", "fitness_rating",
                           "speed_pro", "win_matrix_jockey", "win_matrix_trainer"]
        roadmap_score_dict = MemoryStorage.fetch_by_key(
            MemoryKeyPrefix.ROADMAP_SCORE,
            race_date, race_num, "scores")
        if not roadmap_score_dict:
            logger.error(f"Failed to get roadmap score")
            return pd.DataFrame(columns=required_fields)
        df = pd.DataFrame(roadmap_score_dict).reset_index()
        df = df.rename(columns={"index": "horse_num"})
        df["horse_num"] = df["horse_num"].astype(str)
        for column in required_fields:
            if column not in df.columns:
                df[column] = 0
        df = df.rename(columns={"win_matrix_jockey": "jockey_win_tier",
                                "win_matrix_trainer": "trainer_win_tier",
                                "overbought_statistics": "overbought_score",
                                "win_investment": "win_investment_score",
                                "speed_pro": "speed_pro_score",
                                "cold_door": "cold_door_score",
                                "fitness_rating": "fitness_ratings_score"})
        for columns in ["jockey_win_tier", "trainer_win_tier", "overbought_score", "speed_pro_score",
                        "cold_door_score", "fitness_ratings_score"]:
            df[columns] = df[columns].apply(lambda x: int(x) if x > 0 else 0)

        logger.info(f"Succesfully fetch from Redis")
        return df

    @classmethod
    def get_investment_snapshot(cls, race_date: str, race_num: int, minute_snapshot: int) -> pd.DataFrame:
        required_fields = ["horse_num", "is_invested", "investment_snapshot_win_rate"]
        investment_snapshot_dict = MemoryStorage.fetch_by_key(
            MemoryKeyPrefix.INVESTMENT_SNAPSHOT,
            race_date, race_num, "statistic")
        if not investment_snapshot_dict:
            logger.error(f"Failed to get investment snapshot")
            return pd.DataFrame(columns=required_fields)

        rows = []
        for horse_num, horse_data in investment_snapshot_dict.items():
            snapshot_data = horse_data.get(str(minute_snapshot + 1), {})
            if not snapshot_data:
                rows.append({
                    "horse_num": str(horse_num),
                    "is_invested": False,
                    "investment_snapshot_win_rate": 0
                })
            else:
                is_invested = snapshot_data["is_invested"]
                jockey = snapshot_data["jockey"]
                trainer = snapshot_data["trainer"]
                win_rate = ((jockey[0] + trainer[0]) / (jockey[2] + trainer[2])) if (jockey[2] + trainer[
                    2]) != 0 else 0.0

                if win_rate < 0.1:
                    investment_snapshot_win_rate = 1
                elif win_rate < 0.2:
                    investment_snapshot_win_rate = 2
                elif win_rate < 0.3:
                    investment_snapshot_win_rate = 3
                else:
                    investment_snapshot_win_rate = 4

                rows.append({
                    "horse_num": str(horse_num),
                    "is_invested": is_invested,
                    "investment_snapshot_win_rate": int(investment_snapshot_win_rate)
                })
        df = pd.DataFrame(rows)
        
        logger.info(f"Succesfully fetch from Redis")
        return df

    @classmethod
    def get_win_place(cls, race_date: str, race_num: int) -> pd.DataFrame:
        required_fields = ["horse_num", "win_odds_category", "win_odds"]
        wp_dict = MemoryStorage.fetch_by_key(
            MemoryKeyPrefix.WIN_PLACE_ODDS_SCORE,
            race_date, race_num, "horses")
        if not wp_dict:
            logger.error(f"Failed to get win place score")
            return pd.DataFrame(columns=required_fields)

        df = pd.DataFrame(wp_dict).T[['win']].reset_index()
        df = df.rename(columns={"index": "horse_num"})
        df["win_odds_category"] = df["win"].apply(OddsMapper.win_odds_grouping)
        df["win_investment"] = df["win"].apply(lambda x: 0.825 / x if x > 0 else 0)
        df = df.rename(columns={"win": "win_odds"})
        for column in required_fields:
            if column not in df.columns:
                df[column] = 0
        logger.info(f"Succesfully fetch from Redis")
        return df
    
    @classmethod
    def get_quinella_win_ci(cls, race_date: str, race_num: int) -> pd.DataFrame:
        required_fields = ["horse_num", "quinella_win_ci"]
        qw_dict = MemoryStorage.fetch_by_key(
            MemoryKeyPrefix.QUINELLA_WIN_CI_SCORE,
            race_date, race_num, "statistic")
        if not qw_dict:
            logger.error(f"Failed to get quinella win ci score")
            return pd.DataFrame(columns=required_fields)

        rows = []
        for horse_num, horse_data in qw_dict.items():
            qw_data = horse_data.get("quinella_win_ci", 0)
            if not qw_data:
                rows.append({
                    "horse_num": str(horse_num),
                    "quinella_win_ci": 0
                })
            else:
                rows.append({
                    "horse_num": str(horse_num),
                    "quinella_win_ci": qw_data
                })
        df = pd.DataFrame(rows)
        
        logger.info(f"Succesfully fetch from Redis")
        return df

    @classmethod
    def get_speed_pro(cls, race_date: str, race_num: int) -> pd.DataFrame:
        required_fields = ["horse_num", "speed_pro_top_4_score"]
        speed_pro_dict = MemoryStorage.fetch_by_key(
            MemoryKeyPrefix.SPEED_PRO,
            race_date, race_num, "statistic")
        if not speed_pro_dict:
            logger.error(f"Failed to get speed pro score")
            return pd.DataFrame(columns=required_fields)

        rows = []
        for horse_num, horse_data in speed_pro_dict.items():
            jockey_data = horse_data.get("jockey", {})
            trainer_data = horse_data.get("trainer", {})
            if jockey_data and trainer_data:
                jockey_top_4_percent = jockey_data.get("top4_percentage", 0)
                trainer_top_4_percent = trainer_data.get("top4_percentage", 0)
                if jockey_top_4_percent != 0 and trainer_top_4_percent != 0:
                    total_top_4_percent = jockey_top_4_percent + trainer_top_4_percent
                    if total_top_4_percent < 0.6:
                        score = 0
                    elif total_top_4_percent >= 0.6 and total_top_4_percent < 0.9:
                        score = 1
                    elif total_top_4_percent >= 0.9 and total_top_4_percent < 1.2:
                        score = 2
                    elif total_top_4_percent >= 1.2 and total_top_4_percent <= 1.5:
                        score = 3
                    else:
                        score = 4
                    rows.append({
                        "horse_num": str(horse_num),
                        "speed_pro_top_4_score": score
                    })
                else:
                    rows.append({
                        "horse_num": str(horse_num),
                        "speed_pro_top_4_score": 0
                    })
        df = pd.DataFrame(rows)
        
        logger.info(f"Succesfully fetch from Redis")
        return df
    
    @classmethod
    def get_cold_door(cls, race_date: str, race_num: int) -> pd.DataFrame:
        required_fields = ["horse_num", "cold_door_top_4_score"]
        cold_door_dict = MemoryStorage.fetch_by_key(
            MemoryKeyPrefix.COLD_DOOR,
            race_date, race_num, "statistic")
        if not cold_door_dict:
            logger.error(f"Failed to get cold door score")
            return pd.DataFrame(columns=required_fields)

        rows = []
        for horse_num, horse_data in cold_door_dict.items():
            jockey_data = horse_data.get("jockey", {})
            trainer_data = horse_data.get("trainer", {})
            if jockey_data and trainer_data:
                jockey_top_4_percent = jockey_data.get("top4_percentage", 0)
                trainer_top_4_percent = trainer_data.get("top4_percentage", 0)
                if jockey_top_4_percent != 0 and trainer_top_4_percent != 0:
                    total_top_4_percent = jockey_top_4_percent + trainer_top_4_percent
                    if total_top_4_percent < 0.6:
                        score = 0
                    elif total_top_4_percent >= 0.6 and total_top_4_percent < 0.9:
                        score = 1
                    elif total_top_4_percent >= 0.9 and total_top_4_percent < 1.2:
                        score = 2
                    elif total_top_4_percent >= 1.2 and total_top_4_percent <= 1.5:
                        score = 3
                    else:
                        score = 4
                    rows.append({
                        "horse_num": str(horse_num),
                        "cold_door_top_4_score": score
                    })
                else:
                    rows.append({
                        "horse_num": str(horse_num),
                        "cold_door_top_4_score": 0
                    })
        df = pd.DataFrame(rows)
        
        logger.info(f"Succesfully fetch from Redis")
        return df

    @classmethod
    def get_pool_ratio(cls, race_date: str, race_num: int) -> float:
        pool_dict = MemoryStorage.fetch_by_key(
            MemoryKeyPrefix.POOL_RATIO,
            race_date, race_num, "pools")
        if not pool_dict:
            logger.error(f"Failed to get win place score")
            return 0

        return pool_dict.get("pool_ratio", 0)

    @classmethod
    def get_overbought_from_win_place_ci(cls, race_date: str, race_num: int) -> pd.DataFrame:
        required_fields = ["horse_num", "win_place_ci", "pool_ratio", "is_overbought"]
        wp_dict = MemoryStorage.fetch_by_key(
            MemoryKeyPrefix.WIN_PLACE_CI_SCORE,
            race_date, race_num, "horses")
        if not wp_dict:
            logger.error(f"Failed to get win place ci")
            return pd.DataFrame(columns=required_fields)

        df = pd.DataFrame.from_dict(wp_dict, orient='index', columns=['win_place_ci']).reset_index()
        df = df.rename(columns={"index": "horse_num"})

        df["pool_ratio"] = cls.get_pool_ratio(race_date, race_num)
        df["is_overbought"] = df["win_place_ci"] > df["pool_ratio"]

        for column in required_fields:
            if column not in df.columns:
                df[column] = 0
        return df

    @classmethod
    def get_expected_odds(cls, race_date: str, race_num: int) -> pd.DataFrame:
        required_fields = ["horse_num", "expected_win_odds"]
        expected_win_dict = MemoryStorage.fetch_by_key(
            MemoryKeyPrefix.EXPECTED_WIN_RECORD,
            race_date, race_num, "expected_win_odds")
        if not expected_win_dict:
            logger.error(f"Failed to get expected_win odds")
            return pd.DataFrame(columns=required_fields)

        rows = []
        for horse_num, horse_data in expected_win_dict.items():
            snapshot_data = horse_data.get("latest", None)
            if not snapshot_data:
                rows.append({
                    "horse_num": str(horse_num),
                    "expected_win_odds": 0
                })
            else:
                rows.append({
                    "horse_num": str(horse_num),
                    "expected_win_odds": snapshot_data
                })
        df = pd.DataFrame(rows)
        
        logger.info(f"Succesfully fetch from Redis")
        return df
    
    @classmethod
    def get_loss_detail(cls, race_date: str, race_num: int) -> pd.DataFrame:
        required_fields = ["loss_results"]
        loss_detail_dict = MemoryStorage.fetch_by_key(
            MemoryKeyPrefix.LOSS_DETAIL,
            race_date, race_num, "loss_results")
        if not loss_detail_dict:
            logger.error(f"Failed to get loss detail score")
            return pd.DataFrame(columns=required_fields)
        rows = {}
        winner_results = {}
        loser_results = {}
        for loss_detail_race_num, loss_detail_horse_list in loss_detail_dict.items():
            winner_results[str(loss_detail_race_num)] = []
            loser_results[str(loss_detail_race_num)] = []
            for result in loss_detail_horse_list:
                if result['loss'] is not None:
                    loss_value = int(result['loss'])
                else:
                    loss_value = 0  # Set a default value or handle it according to your requirements
                if result['is_winner']:
                    winner_results[str(loss_detail_race_num)].append({
                        "horse_num": result['horse_num'], 
                        "jockey_code": result['jockey_code']
                    })
                else:
                    loser_results[str(loss_detail_race_num)].append({
                        "horse_num": result['horse_num'], 
                        "jockey_code": result['jockey_code'],
                        "loss": loss_value
                    })
        rows["winner_results"] = winner_results
        rows["loser_results"] = loser_results
        df = pd.DataFrame(rows)
        
        logger.info(f"Succesfully fetch from Redis")
        return df