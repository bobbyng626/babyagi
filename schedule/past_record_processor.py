import pandas as pd
import numpy as np
from utils import OddsMapper, ChineseEnglishMapper
from aexlutils import logger
from utils.oss import OssFetcher
from typing import List
import oss2


class PastRecordProcessor:
    pd.set_option('display.max_columns', None)
    start_date = "2022-09-01"
    jt_tier_dict = {}
    past_grouping = {}
    use_minute = [0, 1]

    top_6_jockeys = ['PZ', 'HCY', 'TEK', 'CML', 'HEL', 'LDE']
    second_6_jockeys = ['BA', 'BH', 'FEL', 'BHW', 'PMF', 'CJE']
    top_6_trainers = ['SJJ', 'LFC', 'LKW', 'CAS', 'YPF', 'SCS']
    second_6_trainers = ['FC', 'MKL', 'WDJ', 'HAD', 'YTP', 'HDA']

    @classmethod
    def update_past_record(cls):
        cls.update_jt_tier()
        cls.get_contrast_df()
        cls.get_diff_df()
        cls.get_expected_ci_df()
        cls.get_expected_qw_df()

    @classmethod
    def update_past_performance(cls):
        cls.update_jt_tier()
        cls.update_expected_odds(minute_snapshot_list=cls.use_minute)
        cls.update_investment_contrast(minute_snapshot_list=cls.use_minute)
        for minute_snapshot in cls.use_minute:
            for run_top4 in [False, True]:
                cls.process_past_performance(minute_snapshot=minute_snapshot, run_top4=run_top4).to_csv(
                    f"past_performanc{'e' if not run_top4 else 'e_top4'}_{minute_snapshot}min.csv", index=False)

    @classmethod
    def update_jt_tier(cls):
        jt_top4_dict = OssFetcher.get_json_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path=OssFetcher.JT_TIER_TOP4)
        jt_win_dict = OssFetcher.get_json_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path=OssFetcher.JT_TIER)
        if jt_top4_dict is None or jt_win_dict is None:
            return None

        jockey_win_list = jt_win_dict.get("jockeys", [])
        jockey_top4_list = jt_top4_dict.get("jockeys", [])
        jockey_filter_list = ["MOJ", "DSS", "BV"]

        trainer_win_list = jt_win_dict.get("trainers", [])
        trainer_top4_list = jt_top4_dict.get("trainers", [])
        trainer_filter_list = []

        if not jockey_win_list or not jockey_top4_list or not trainer_win_list or not trainer_top4_list:
            logger.error("Failed to get jockey or trainer list")
            return None

        result_jockey_win_list = [elem for elem in jockey_win_list if elem not in jockey_filter_list]
        result_jockey_top4_list = [elem for elem in jockey_top4_list if elem not in jockey_filter_list]
        result_trainer_win_list = [elem for elem in trainer_win_list if elem not in trainer_filter_list]
        result_trainer_top4_list = [elem for elem in trainer_top4_list if elem not in trainer_filter_list]

        if not result_jockey_win_list or not result_jockey_top4_list \
                or not result_trainer_win_list or not result_trainer_top4_list:
            logger.error("Failed to get filtered jockey or trainer list")
            return None

        cls.jt_tier_dict["top_6_jockeys"] = result_jockey_win_list[0:6]
        cls.jt_tier_dict["second_6_jockeys"] = result_jockey_win_list[6:12]
        cls.jt_tier_dict["top_6_trainers"] = result_trainer_win_list[0:6]
        cls.jt_tier_dict["second_6_trainers"] = result_trainer_win_list[6:12]

        cls.jt_tier_dict["top_6_jockeys_top4"] = result_jockey_top4_list[0:6]
        cls.jt_tier_dict["second_6_jockeys_top4"] = result_jockey_top4_list[6:12]
        cls.jt_tier_dict["top_6_trainers_top4"] = result_trainer_top4_list[0:6]
        cls.jt_tier_dict["second_6_trainers_top4"] = result_trainer_top4_list[6:12]
        logger.info(f"Updated jt tier: {cls.jt_tier_dict}")

    @classmethod
    def update_expected_odds(cls, minute_snapshot_list: list):
        df_past_performance_full = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_FEATURE_STORE,
            object_path=OssFetcher.PAST_PERFORMANCE)
        if df_past_performance_full.empty:
            logger.error("Failed to get past performance")
            return None
        for minute_snapshot in minute_snapshot_list:
            df_past_performance = df_past_performance_full.copy()
            df_past_performance = \
                df_past_performance[df_past_performance["time_diff"] == minute_snapshot].reset_index(drop=True)

            df_past_performance = df_past_performance[[
                "race_date", "race_num", "horse_num", "jockey_code", "trainer_code",
                "place_num", "win_place_ci", "pool_ratio"]]

            df_past_performance["is_top_1"] = df_past_performance["place_num"] == 1
            df_past_performance["is_overbought"] = df_past_performance["pool_ratio"] < df_past_performance[
                "win_place_ci"]

            df_past_performance['ci_group'] = (df_past_performance['win_place_ci'] // 0.1).astype(int)
            df_past_performance['ci_group'] = df_past_performance['ci_group'].apply(
                lambda x: f"{round(x / 10, 1)}-{round(x / 10 + 0.1, 1)}")

            df_jockey = df_past_performance.groupby(["jockey_code", "is_overbought", "ci_group"])["is_top_1"].agg([
                ("hit_count", "sum"),
                ("race_count", "count"),
                ("percentage", "mean"),
                ("percent",
                 lambda x: f"{int((round(x.mean(), 2)) * 100)}% ({round(x.sum(), 2)}/{round(x.count(), 2)})")]
            ).reset_index()
            OssFetcher.put_df_as_csv_to_bucket(
                df=df_jockey,
                file_name=f"expected_ci/expected_ci_jockey_{minute_snapshot}min.csv",
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE)
            logger.info(f"Put jockey ci {minute_snapshot} min into {OssFetcher.BUCKET_READ_LAKEHOUSE}")
            df_trainer = df_past_performance.groupby(["trainer_code", "is_overbought", "ci_group"])["is_top_1"].agg([
                ("hit_count", "sum"),
                ("race_count", "count"),
                ("percentage", "mean"),
                ("percent",
                 lambda x: f"{int((round(x.mean(), 2)) * 100)}% ({round(x.sum(), 2)}/{round(x.count(), 2)})")]
            ).reset_index()
            OssFetcher.put_df_as_csv_to_bucket(
                df=df_trainer,
                file_name=f"expected_ci/expected_ci_trainer_{minute_snapshot}min.csv",
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE)
            logger.info(f"Put trainer ci {minute_snapshot} min into {OssFetcher.BUCKET_READ_LAKEHOUSE}")

    @classmethod
    def update_investment_contrast(cls, minute_snapshot_list: list):
        df_past_performance_full = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_FEATURE_STORE,
            object_path=OssFetcher.PAST_PERFORMANCE)
        if df_past_performance_full.empty:
            logger.error("Failed to get past performance")
            return None
        for minute_snapshot in minute_snapshot_list:
            df_past_performance = df_past_performance_full.copy()
            df_past_performance = \
                df_past_performance[df_past_performance["time_diff"] == minute_snapshot].reset_index(drop=True)

            df_past_performance = df_past_performance[[
                "race_date", "race_num", "horse_num", "jockey_code", "trainer_code",
                "place_num", "win_odds"]]

            df_past_performance["is_top_1"] = df_past_performance["place_num"] == 1
            df_past_performance["win_investment"] = 0.825 / df_past_performance["win_odds"]
            df_past_performance['hot'] = df_past_performance.groupby(['race_date', 'race_num'])['win_odds'].rank(
                method="min")

            group_num = 4
            label_list = ["VERY LOW", "LOW", "HIGH", "VERY HIGH"]

            df_investment_ratio = df_past_performance.groupby(["race_date", "race_num"])['win_investment'].agg([
                ("invest_1_over_2", lambda x: (x.nlargest(1)) - (x.nlargest(2).iloc[-1])),
                ("invest_2_over_3", lambda x: (x.nlargest(2).iloc[-1]) - (x.nlargest(3).iloc[-1])),
                ("invest_3_over_4", lambda x: (x.nlargest(3).iloc[-1]) - (x.nlargest(4).iloc[-1]))
            ]).reset_index()

            past_grouping = {}
            for ratio in ["invest_1_over_2", "invest_2_over_3", "invest_3_over_4"]:
                df_investment_ratio[f"{ratio}_group"], bin_list = pd.qcut(df_investment_ratio[ratio], q=group_num,
                                                                          labels=label_list, retbins=True)
                past_grouping[ratio] = bin_list
            cls.past_grouping = past_grouping

            df_past_performance = df_past_performance.merge(df_investment_ratio,
                                                            on=["race_date", "race_num"], how="left")

            df_jockey = df_past_performance[df_past_performance["hot"] <= 8].groupby(
                ["jockey_code", "hot", "invest_1_over_2_group"])["is_top_1"].agg([
                ("hit_count", "sum"),
                ("race_count", "count"),
                ("percentage", "mean"),
                ("percent",
                 lambda x: f"{int((round(x.mean(), 2)) * 100)}% ({round(x.sum(), 2)}/{round(x.count(), 2)})"),
            ]).reset_index()

            OssFetcher.put_df_as_csv_to_bucket(
                df=df_jockey,
                file_name=f"investment_contrast/evaluation_win_contrast_jockey_{minute_snapshot}min.csv",
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE)
            logger.info(f"Put jockey contrast {minute_snapshot} min into {OssFetcher.BUCKET_READ_LAKEHOUSE}")

            df_trainer = df_past_performance[df_past_performance["hot"] <= 8].groupby(
                ["trainer_code", "hot", "invest_1_over_2_group"])["is_top_1"].agg([
                ("hit_count", "sum"),
                ("race_count", "count"),
                ("percentage", "mean"),
                ("percent",
                 lambda x: f"{int((round(x.mean(), 2)) * 100)}% ({round(x.sum(), 2)}/{round(x.count(), 2)})"),
            ]).reset_index()

            OssFetcher.put_df_as_csv_to_bucket(
                df=df_trainer,
                file_name=f"investment_contrast/evaluation_win_contrast_trainer_{minute_snapshot}min.csv",
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE)
            logger.info(f"Put trainer contrast {minute_snapshot} min into {OssFetcher.BUCKET_READ_LAKEHOUSE}")

    @classmethod
    def process_past_performance(cls, minute_snapshot: int, run_top4: bool) -> pd.DataFrame():
        # get past performance
        df_past_performance = cls.get_past_record_df(minute_snapshot)
        if df_past_performance.empty:
            logger.error("Failed to get past performance")
            return None

        # version 1 past ranking category
        # get jt performance
        df_jockey_performance = cls.get_jockey_performance(run_top4=run_top4)
        df_trainer_performance = cls.get_trainer_performance(run_top4=run_top4)
        if df_jockey_performance.empty or df_trainer_performance.empty:
            logger.error("Failed to get jockey or trainer performance")
            return None

        # merge jockey and trainer performance
        df_past_performance = df_past_performance.merge(
            df_jockey_performance,
            on=["jockey_code", "win_odds_category", "win_place_ci_category", "quinella_win_ci_category"],
            how="left")

        df_past_performance = df_past_performance.merge(
            df_trainer_performance,
            on=["trainer_code", "win_odds_category", "win_place_ci_category", "quinella_win_ci_category"],
            how="left")

        # version 2 race distribution
        df_jockey_gain, df_trainer_gain = cls.get_jt_gain_df()
        if df_jockey_gain.empty or df_trainer_gain.empty:
            logger.error("Failed to get jockey or trainer gain")
            return None

        df_past_performance = df_past_performance.merge(
            df_jockey_gain, on=["race_date", "race_num", 'jockey_code'], how='left')
        df_past_performance["jockey_gain"] = df_past_performance["jockey_gain"].fillna(0)

        df_past_performance = df_past_performance.merge(
            df_trainer_gain, on=["race_date", "race_num", 'trainer_code'], how='left')
        df_past_performance["trainer_gain"] = df_past_performance["trainer_gain"].fillna(0)

        # get wi and ob category dict #
        wi_dict = cls.get_wi_dict()
        ob_dict = cls.get_ob_dict(run_top4=run_top4)
        if None in [wi_dict, ob_dict]:
            logger.error("Failed to get wi or ob dict")
            return None

        df_past_performance[f"wi_tier"] = np.vectorize(cls.get_grouping_dict)(
            wi_dict, df_past_performance['jockey_code'], df_past_performance['trainer_code'],
            df_past_performance['win_odds_category'], df_past_performance["investment_difference_3_latest"])
        cls.separate_column(df_past_performance, "wi")
        df_past_performance.drop("wi_tier", axis=1)

        df_past_performance["wi_score"] = np.vectorize(OddsMapper.get_df_wi_score)(
            df_past_performance['jockey_wi_win_percentage'], df_past_performance['trainer_wi_win_percentage'])

        df_past_performance[f"overbought_tier"] = np.vectorize(cls.get_grouping_dict)(
            ob_dict, df_past_performance['jockey_code'], df_past_performance['trainer_code'],
            df_past_performance['win_odds_category'], df_past_performance["overbought_ci"])
        cls.separate_column(df_past_performance, "overbought")
        df_past_performance.drop("overbought_tier", axis=1)

        if run_top4:
            df_past_performance["overbought_score"] = np.vectorize(OddsMapper.get_df_score_top4)(
                df_past_performance['jockey_overbought_win_percentage'],
                df_past_performance['trainer_overbought_win_percentage'])
        else:
            df_past_performance["overbought_score"] = np.vectorize(OddsMapper.get_df_score)(
                df_past_performance['jockey_overbought_win_percentage'],
                df_past_performance['trainer_overbought_win_percentage'])

        df_speed_pro, df_fitness = cls.get_speed_pro_and_fitness_df()
        df_cold_door = cls.get_cold_door_df()
        if df_speed_pro.empty or df_fitness.empty or df_cold_door.empty:
            logger.error("Failed to get speed pro df")
            return None

        df_past_performance = df_past_performance.merge(
            df_speed_pro, on=["race_date", "race_num", "horse_num"], how="left")

        df_past_performance = df_past_performance.merge(
            df_fitness, on=["race_date", "race_num", "horse_num"], how="left")

        df_past_performance = df_past_performance.merge(
            df_cold_door, on=["race_date", "race_num", "horse_num"], how="left")

        # version 3
        df_win_investment_snapshot = cls.get_wi_snapshot_df(minute_snapshot)
        if df_win_investment_snapshot.empty:
            logger.error("Failed to get win investment snapshot df")
            return None

        df_past_performance = df_past_performance.merge(
            df_win_investment_snapshot, on=["race_date", "race_num", "horse_num"], how="left")
        df_past_performance["is_invested"] = df_past_performance["is_invested"].fillna(False)

        df_jockey_investment_snapshot, df_trainer_investment_snapshot = cls.get_wi_snapshot_df_jt_percent(
            minute_snapshot=minute_snapshot, run_top4=run_top4)
        if df_jockey_investment_snapshot.empty or df_trainer_investment_snapshot.empty:
            logger.error("Failed to get win investment snapshot jt df")
            return None

        df_past_performance = df_past_performance.merge(
            df_jockey_investment_snapshot, on=["jockey_code", "win_odds_category", "is_invested"], how="left")

        df_past_performance = df_past_performance.merge(
            df_trainer_investment_snapshot, on=["trainer_code", "win_odds_category", "is_invested"], how="left")

        if run_top4:
            df_past_performance["investment_snapshot_win_rate"] = np.vectorize(OddsMapper.get_df_wi_score_top4)(
                df_past_performance['jockey_win_snapshot_percent'],
                df_past_performance['trainer_win_snapshot_percent'])
        else:
            df_past_performance["investment_snapshot_win_rate"] = np.vectorize(OddsMapper.get_df_wi_score)(
                df_past_performance['jockey_win_snapshot_percent'],
                df_past_performance['trainer_win_snapshot_percent'])

        for columns in ["jockey_win_snapshot_percent", "trainer_win_snapshot_percent"]:
            df_past_performance[columns] = df_past_performance[columns].fillna(0)

        # version 4
        df_speed_pro_jockey, df_speed_pro_trainer = cls.get_speed_pro_jt_df(run_top4=run_top4)
        df_cold_door_jockey, df_cold_door_trainer = cls.get_cold_door_jt_df(run_top4=run_top4)
        df_fitness_jockey, df_fitness_trainer = cls.get_fitness_jt_df(run_top4=run_top4)

        if df_speed_pro_jockey.empty or df_speed_pro_trainer.empty or \
                df_cold_door_jockey.empty or df_cold_door_trainer.empty or \
                df_fitness_jockey.empty or df_fitness_trainer.empty:
            logger.error("Failed to get speed pro df")
            return None
        df_past_performance = df_past_performance.merge(df_speed_pro_jockey,
                                                        on=["win_odds_category", "jockey_code", "speed_pro_category"],
                                                        how="left")
        df_past_performance = df_past_performance.merge(df_speed_pro_trainer,
                                                        on=["win_odds_category", "trainer_code", "speed_pro_category"],
                                                        how="left")

        df_past_performance = df_past_performance.merge(df_cold_door_jockey,
                                                        on=["win_odds_category", "jockey_code", "cold_door_rating"],
                                                        how="left")
        df_past_performance = df_past_performance.merge(df_cold_door_trainer,
                                                        on=["win_odds_category", "trainer_code", "cold_door_rating"],
                                                        how="left")

        df_past_performance = df_past_performance.merge(df_fitness_jockey,
                                                        on=["win_odds_category", "jockey_code", "fitness_ratings"],
                                                        how="left")
        df_past_performance = df_past_performance.merge(df_fitness_trainer,
                                                        on=["win_odds_category", "trainer_code", "fitness_ratings"],
                                                        how="left")

        for columns in ["speed_pro_jockey_win_percent", "speed_pro_trainer_win_percent",
                        "cold_door_jockey_win_percent", "cold_door_trainer_win_percent",
                        "fitness_ratings_jockey_win_percent", "fitness_ratings_trainer_win_percent"]:
            df_past_performance[columns] = df_past_performance[columns].fillna(0)

        if run_top4:
            df_past_performance["speed_pro_score"] = np.vectorize(OddsMapper.get_df_score_top4)(
                df_past_performance['speed_pro_jockey_win_percent'],
                df_past_performance['speed_pro_trainer_win_percent'])
            df_past_performance["cold_door_score"] = np.vectorize(OddsMapper.get_df_score_top4)(
                df_past_performance['cold_door_jockey_win_percent'],
                df_past_performance['cold_door_trainer_win_percent'])
            df_past_performance["fitness_ratings_score"] = np.vectorize(OddsMapper.get_df_score_top4)(
                df_past_performance['fitness_ratings_jockey_win_percent'],
                df_past_performance['fitness_ratings_trainer_win_percent'])
        else:
            df_past_performance["speed_pro_score"] = np.vectorize(OddsMapper.get_df_score)(
                df_past_performance['speed_pro_jockey_win_percent'],
                df_past_performance['speed_pro_trainer_win_percent'])
            df_past_performance["cold_door_score"] = np.vectorize(OddsMapper.get_df_score)(
                df_past_performance['cold_door_jockey_win_percent'],
                df_past_performance['cold_door_trainer_win_percent'])
            df_past_performance["fitness_ratings_score"] = np.vectorize(OddsMapper.get_df_score)(
                df_past_performance['fitness_ratings_jockey_win_percent'],
                df_past_performance['fitness_ratings_trainer_win_percent'])

        df_decision_tree = cls.get_decision_tree_df()
        if df_decision_tree.empty:
            logger.error("Failed to get decision tree df")
            return None
        df_past_performance = df_past_performance.merge(df_decision_tree, on=["race_date", "race_num"], how="left")
        df_past_performance['is_reborn'] = np.vectorize(OddsMapper.get_bool_reborn_eliminate)(
            df_past_performance['horse_num'],
            df_past_performance['reborn'])
        df_past_performance['is_deselect'] = np.vectorize(OddsMapper.get_bool_reborn_eliminate)(
            df_past_performance['horse_num'],
            df_past_performance['deselected'])

        # get result
        df_dividend = cls.get_dividend_df()
        if df_dividend.empty:
            logger.error("Failed to get dividend df")
            return None
        df_past_performance = df_past_performance.merge(df_dividend, on=['race_date', 'race_num'], how="left")

        df_past_performance = df_past_performance.drop_duplicates(subset=['race_date', 'race_num', "horse_num"])

        df_result = df_past_performance.groupby(['race_date', 'race_num']) \
            .apply(lambda x: x[x["place_num"] <= 4].sort_values('place_num')['horse_num'].tolist()).reset_index(
        ).rename(columns={0: 'result'})

        df_hot_ascending = df_past_performance.groupby(['race_date', 'race_num']) \
            .apply(lambda x: x.sort_values('win_odds')['horse_num'].tolist()).reset_index().rename(
            columns={0: 'hot_ascending'})

        df_past_performance = df_past_performance.merge(df_result, on=['race_date', 'race_num'], how="left")
        df_past_performance = df_past_performance.merge(df_hot_ascending, on=['race_date', 'race_num'], how="left")
        df_past_performance["speed_pro_energy_diff"] = df_past_performance["speed_pro_energy_diff"].fillna(0).apply(
            lambda x: int(x))
        df_past_performance["speed_pro_category"] = df_past_performance["speed_pro_category"].fillna(0).apply(
            lambda x: int(x))
        df_past_performance["cold_door_rating"] = df_past_performance["cold_door_rating"].fillna(0).apply(
            lambda x: int(x))
        df_past_performance["fitness_ratings"] = df_past_performance["fitness_ratings"].fillna(0).apply(
            lambda x: int(x))
        df_past_performance["fitness_ratings_score"] = df_past_performance["fitness_ratings_score"].fillna(0).apply(
            lambda x: int(x))

        df_expected_win_odds = cls.get_expected_win_df()
        if df_expected_win_odds.empty:
            logger.error("Failed to get expected win odds df")
            return None
        df_past_performance = df_past_performance.merge(
            df_expected_win_odds, on=["race_date", "race_num", "horse_num"], how="left")

        df_past_performance["normalised_win_odds"] = df_past_performance["normalised_win_odds"].fillna(0)

        df_past_performance["win_dd_ratio"] = df_past_performance["normalised_win_odds"] / df_past_performance[
            "win_odds"]
        df_past_performance["win_dd_ratio_group"] = df_past_performance["win_dd_ratio"].apply(
            lambda x: 1 if x <= 0.9 else 2 if x <= 1.1 else 3)

        df_past_performance["win_odds_diff"] = df_past_performance["normalised_win_odds"] - \
                                               df_past_performance["win_odds"]

        # Calculate the threshold as 5% of 'win_odds'
        df_past_performance["win_odds_diff_threshold"] = 0.05 * df_past_performance['win_odds']

        df_past_performance['win_odds_diff_group'] = np.where(
            df_past_performance['win_odds_diff'] > df_past_performance["win_odds_diff_threshold"], 'More',
            np.where(df_past_performance['win_odds_diff'] < -df_past_performance["win_odds_diff_threshold"], 'Less',
                     'Similar'))

        df_past_performance['ci_group'] = (df_past_performance['win_place_ci'] // 0.1).astype(int)
        df_past_performance['ci_group'] = df_past_performance['ci_group'].apply(
            lambda x: f"{round(x / 10, 1)}-{round(x / 10 + 0.1, 1)}")

        df_past_performance['qw_group'] = (df_past_performance['quinella_win_ci'] // 0.1).astype(int)
        df_past_performance['qw_group'] = df_past_performance['qw_group'].apply(
            lambda x: f"{round(x / 10, 1)}-{round(x / 10 + 0.1, 1)}")

        OssFetcher.put_df_as_csv_to_bucket(
            df=df_past_performance,
            file_name=f"llm-prompt-service/past-record/"
                      f"past_performanc{'e' if not run_top4 else 'e_top4'}_{minute_snapshot}min.csv",
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE)
        logger.info(f"Successfully updated past record in oss")
        return df_past_performance

    @classmethod
    def get_past_record_df(cls, minute_snapshot: int) -> pd.DataFrame():
        df_past_performance = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_FEATURE_STORE,
            object_path=OssFetcher.PAST_PERFORMANCE)
        if df_past_performance.empty:
            logger.error("Failed to get past performance")
            return None

        # filter past performance with time
        df_past_performance = df_past_performance[
            df_past_performance["time_diff"] == minute_snapshot].reset_index(drop=True)

        # get place into string
        df_past_performance["place_num_str"] = df_past_performance["place_num"].apply(
            lambda x: "bad" if x > 4 else "average" if x > 2 else "good")

        df_past_performance["is_overbought"] = df_past_performance["pool_ratio"] < df_past_performance["win_place_ci"]

        df_past_performance['investment_tier'] = df_past_performance['investment_difference_3_latest'].apply(
            lambda x: 4 if x > 0.3 else 3 if x > 0.15 else 2 if x > 0 else 1)

        df_past_performance["pool_ratio_group"] = df_past_performance["pool_ratio"].apply(
            OddsMapper.pool_ratio_grouping)

        df_past_performance["win_investment"] = 0.825 / df_past_performance["win_odds"]
        df_top3 = df_past_performance.groupby(["race_date", "race_num"])["win_investment"].nlargest(3).groupby(
            ["race_date", "race_num"]).sum().reset_index().rename(columns={"win_investment": "top3_investment"})
        df_past_performance = df_past_performance.merge(df_top3, on=['race_date', 'race_num'], how='left')
        df_past_performance["top3_investment_group"] = df_past_performance["top3_investment"].apply(
            OddsMapper.top3_investment_grouping)

        df_past_performance['place_num'] = df_past_performance['place_num'].apply(lambda x: int(x))
        df_past_performance = df_past_performance[
            df_past_performance['race_date'] >= cls.start_date].reset_index(drop=True)
        df_past_performance = df_past_performance.drop_duplicates(subset=['race_date', 'race_num', 'horse_num'])
        df_past_performance["horse_count"] = df_past_performance.groupby(['race_date', 'race_num'])[
            'horse_num'].transform('count')
        df_past_performance["race_class"] = df_past_performance["race_class"].apply(
            ChineseEnglishMapper.map_race_class_to_group)
        df_past_performance = df_past_performance[[
            "race_date", "race_num", "horse_num", "horse_code", "jockey_code", "trainer_code",
            "place_num", "place_num_str", "win_odds", "horse_count", "race_class", "win_place_ci", "quinella_win_ci",
            "win_odds_category", "win_place_ci_category", "quinella_win_ci_category",
            "pool_ratio_group", "top3_investment_group",
            "investment_difference_3_latest", "investment_tier", "win_investment",
            "overbought_ci", "is_overbought"]]
        return df_past_performance

    @classmethod
    def get_processed_past_record_df(cls, minute_snapshot: int, run_top4: bool):
        try:
            df_past_performance = OssFetcher.get_df_from_oss(
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
                object_path=f"llm-prompt-service/past-record/"
                            f"past_performanc{'e' if not run_top4 else 'e_top4'}_{minute_snapshot}min.csv")
            df_past_performance.to_csv(
                f"past_performanc{'e' if not run_top4 else 'e_top4'}_{minute_snapshot}min.csv", index=False)
        except oss2.exceptions.NoSuchKey:
            cls.update_past_performance()

    @classmethod
    def get_contrast_df(cls) -> pd.DataFrame():
        df_contrast_jockey = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path="investment_contrast/evaluation_win_contrast_jockey_0min.csv")
        df_contrast_trainer = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path="investment_contrast/evaluation_win_contrast_trainer_0min.csv")

        if df_contrast_jockey.empty or df_contrast_trainer.empty:
            return None
        df_contrast_jockey = df_contrast_jockey[df_contrast_jockey["race_count"] >= 5]
        df_contrast_jockey = df_contrast_jockey[
            ["jockey_code", "hot", "invest_1_over_2_group", "hit_count", "race_count"]]
        df_contrast_jockey = df_contrast_jockey.rename(columns={"hit_count": "jockey_contrast_win",
                                                                "race_count": "jockey_contrast_count"})

        df_contrast_trainer = df_contrast_trainer[df_contrast_trainer["race_count"] >= 5].drop("percent", axis=1)
        df_contrast_trainer = df_contrast_trainer[
            ["trainer_code", "hot", "invest_1_over_2_group", "hit_count", "race_count"]]
        df_contrast_trainer = df_contrast_trainer.rename(columns={"hit_count": "trainer_contrast_win",
                                                                  "race_count": "trainer_contrast_count"})

        return df_contrast_jockey, df_contrast_trainer

    @classmethod
    def get_diff_df(cls) -> pd.DataFrame():
        df_contrast_trainer = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path="win_contrast/ratio_trainer_top1_1.csv")
        if df_contrast_trainer.empty:
            return None
        df_contrast_trainer = df_contrast_trainer[df_contrast_trainer["race_count"] >= 4].drop("percent", axis=1)
        df_contrast_trainer = df_contrast_trainer.rename(columns={"hit_count": "trainer_dd_win",
                                                                  "race_count": "trainer_dd_count",
                                                                  "percentage": "trainer_dd_percentage"})
        df_contrast_trainer["trainer_dd_percentage_group"] = df_contrast_trainer["trainer_dd_percentage"].apply(
            lambda x: 1 if x <= 0.15 else 2 if x <= 0.3 else 3)
        return df_contrast_trainer

    @classmethod
    def get_expected_ci_df(cls) -> pd.DataFrame():
        df_expected_ci_jockey = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path="expected_ci/expected_ci_jockey_0min.csv")
        df_expected_ci_trainer = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path="expected_ci/expected_ci_trainer_0min.csv")
        if df_expected_ci_jockey.empty or df_expected_ci_trainer.empty:
            return None
        df_expected_ci_jockey = df_expected_ci_jockey[df_expected_ci_jockey["race_count"] >= 5]
        df_expected_ci_jockey = df_expected_ci_jockey[
            ["jockey_code", "is_overbought", "ci_group", "hit_count", "race_count"]]
        df_expected_ci_jockey = df_expected_ci_jockey.rename(columns={"hit_count": "jockey_expected_ci_win",
                                                                      "race_count": "jockey_expected_ci_count"})

        df_expected_ci_trainer = df_expected_ci_trainer[df_expected_ci_trainer["race_count"] >= 5]
        df_expected_ci_trainer = df_expected_ci_trainer[
            ["trainer_code", "is_overbought", "ci_group", "hit_count", "race_count"]]
        df_expected_ci_trainer = df_expected_ci_trainer.rename(columns={"hit_count": "trainer_expected_ci_win",
                                                                        "race_count": "trainer_expected_ci_count"})

        return df_expected_ci_jockey, df_expected_ci_trainer

    @classmethod
    def get_expected_qw_df(cls) -> pd.DataFrame():
        df_expected_qw_jockey = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path="expected_qw/expected_qw_jockey_0min.csv")
        df_expected_qw_trainer = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path="expected_qw/expected_qw_trainer_0min.csv")
        if df_expected_qw_jockey.empty or df_expected_qw_trainer.empty:
            return None
        df_expected_qw_jockey = df_expected_qw_jockey[df_expected_qw_jockey["race_count"] >= 5]
        df_expected_qw_jockey = df_expected_qw_jockey[
            ["jockey_code", "win_odds_category", "qw_group", "hit_count", "race_count"]]
        df_expected_qw_jockey = df_expected_qw_jockey.rename(columns={"hit_count": "jockey_expected_qw_win",
                                                                      "race_count": "jockey_expected_qw_count"})

        df_expected_qw_trainer = df_expected_qw_trainer[df_expected_qw_trainer["race_count"] >= 5]
        df_expected_qw_trainer = df_expected_qw_trainer[
            ["trainer_code", "win_odds_category", "qw_group", "hit_count", "race_count"]]
        df_expected_qw_trainer = df_expected_qw_trainer.rename(columns={"hit_count": "trainer_expected_qw_win",
                                                                        "race_count": "trainer_expected_qw_count"})

        return df_expected_qw_jockey, df_expected_qw_trainer

    @classmethod
    def get_expected_win_df(cls) -> pd.DataFrame():
        df_expected_win = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path=OssFetcher.EXPECTED_WIN)
        if df_expected_win.empty:
            return None
        df_expected_win = df_expected_win[["race_date", "race_num", "horse_num", "normalised_win_odds"]]
        return df_expected_win

    @classmethod
    def get_dividend_df(cls) -> pd.DataFrame():
        result_list = OssFetcher.get_json_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_FEATURE_STORE,
            object_path=OssFetcher.DIVIDEND)
        if not result_list:
            logger.error("Failed to get dividend")
            return None
        df_result = pd.DataFrame(columns=['race_date', 'race_num', 'dividend'])
        for race_dict in result_list:
            dividend_list = cls.get_dividend_from_response(race_dict.get('dividend_odds', {}))
            new_row = pd.DataFrame({'race_date': race_dict["race_date"],
                                    "race_num": race_dict["race_num"],
                                    "dividend": [dividend_list]})
            df_result = pd.concat([df_result, new_row], ignore_index=True)
        return df_result

    @classmethod
    def get_jockey_performance(cls, run_top4: bool) -> pd.DataFrame():
        df_jockey_performance = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_FEATURE_STORE,
            object_path=OssFetcher.JOCKEY_PERFORMANCE)
        if df_jockey_performance.empty:
            logger.error("Failed to get jockey performance")
            return None
        if run_top4:
            # find jockey tier by top4 category
            df_jockey_performance['jockey_tier'] = df_jockey_performance['jockey_code'].apply(
                lambda x: 3 if x in cls.jt_tier_dict.get("top_6_jockeys_top4", [])
                else 2 if x in cls.jt_tier_dict.get("second_6_jockeys", []) else 1)
            df_jockey_performance["jockey_win_tier"] = (
                    (df_jockey_performance["1.0"] + df_jockey_performance["2.0"] +
                     df_jockey_performance["3.0"] + df_jockey_performance["4.0"])
                    / df_jockey_performance["total"]).apply(OddsMapper.top4_tier_percent)
        else:
            # find jockey tier by win category
            df_jockey_performance['jockey_tier'] = df_jockey_performance['jockey_code'].apply(
                lambda x: 3 if x in cls.jt_tier_dict.get("top_6_jockeys", [])
                else 2 if x in cls.jt_tier_dict.get("second_6_jockeys", []) else 1)
            df_jockey_performance["jockey_win_tier"] = (
                    df_jockey_performance["1.0"] / df_jockey_performance["total"]).apply(OddsMapper.win_tier_percent)
        return df_jockey_performance[
            ["jockey_code", "win_odds_category", "win_place_ci_category", "quinella_win_ci_category", "jockey_tier",
             "jockey_win_tier"]]

    @classmethod
    def get_trainer_performance(cls, run_top4: bool) -> pd.DataFrame():
        df_trainer_performance = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_FEATURE_STORE,
            object_path=OssFetcher.TRAINER_PERFORMANCE)
        if df_trainer_performance.empty:
            logger.error("Failed to get trainer performance")
            return None
        if run_top4:
            # find trainer tier by top4 category
            df_trainer_performance['trainer_tier'] = df_trainer_performance['trainer_code'].apply(
                lambda x: 3 if x in cls.jt_tier_dict.get("top_6_trainers_top4", [])
                else 2 if x in cls.jt_tier_dict.get("second_6_trainers_top4", []) else 1)
            df_trainer_performance["trainer_win_tier"] = (
                    (df_trainer_performance["1.0"] + df_trainer_performance["2.0"] +
                     df_trainer_performance["3.0"] + df_trainer_performance["4.0"])
                    / df_trainer_performance["total"]).apply(OddsMapper.top4_tier_percent)
        else:
            # find trainer tier by win category
            df_trainer_performance['trainer_tier'] = df_trainer_performance['trainer_code'].apply(
                lambda x: 3 if x in cls.jt_tier_dict.get("top_6_trainers", [])
                else 2 if x in cls.jt_tier_dict.get("second_6_trainers", []) else 1)
            df_trainer_performance["trainer_win_tier"] = (
                    df_trainer_performance["1.0"] / df_trainer_performance["total"]).apply(OddsMapper.win_tier_percent)
        return df_trainer_performance[
            ["trainer_code", "win_odds_category", "win_place_ci_category", "quinella_win_ci_category", "trainer_tier",
             "trainer_win_tier"]]

    @classmethod
    def get_jt_gain_df(cls) -> (pd.DataFrame, pd.DataFrame):
        df_jockey_gain = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path=OssFetcher.JOCKEY_GAIN)
        df_trainer_gain = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path=OssFetcher.TRAINER_GAIN)
        if df_jockey_gain.empty or df_trainer_gain.empty:
            logger.error("Failed to get jockey or trainer gain")
            return None
        df_jockey_gain = df_jockey_gain.rename(columns={"gain": "jockey_gain"})
        df_trainer_gain = df_trainer_gain.rename(columns={"gain": "trainer_gain"})
        return df_jockey_gain, df_trainer_gain

    @classmethod
    def get_speed_pro_and_fitness_df(cls) -> pd.DataFrame():
        # from 2023-02-15
        df_speed_pro = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_FEATURE_STORE,
            object_path=OssFetcher.SPEED_PRO)
        if df_speed_pro.empty:
            logger.error("Failed to get speed pro")
            return None
        df_fitness = df_speed_pro[["race_date", "race_num", "horse_num", "fitness_ratings"]]
        df_speed_pro = df_speed_pro[["race_date", "race_num", "horse_num", "speed_pro_energy_diff"]]
        df_speed_pro["speed_pro_category"] = df_speed_pro["speed_pro_energy_diff"].apply(
            lambda x: 1 if x >= 2 else 2 if x >= -1 else 3 if x >= -3 else 4)
        df_speed_pro["speed_pro_energy_diff"] = df_speed_pro["speed_pro_energy_diff"].apply(lambda x: 0 if x < 0 else x)
        return df_speed_pro, df_fitness

    @classmethod
    def get_cold_door_df(cls) -> pd.DataFrame():
        # from 2023-02-22
        df_cold_door = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_FEATURE_STORE,
            object_path=OssFetcher.COLD_DOOR)
        if df_cold_door.empty:
            logger.error("Failed to get cold door")
            return None
        df_cold_door = df_cold_door.rename(columns={"score": "cold_door_rating"})

        return df_cold_door

    @classmethod
    def get_speed_pro_jt_df(cls, run_top4: bool) -> pd.DataFrame():
        if run_top4:
            df_speed_pro_jockey = OssFetcher.get_df_from_oss(
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
                object_path=OssFetcher.SPEED_PRO_JOCKEY_TOP4)
            df_speed_pro_trainer = OssFetcher.get_df_from_oss(
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
                object_path=OssFetcher.SPEED_PRO_TRAINER_TOP4)
        else:
            df_speed_pro_jockey = OssFetcher.get_df_from_oss(
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
                object_path=OssFetcher.SPEED_PRO_JOCKEY)
            df_speed_pro_trainer = OssFetcher.get_df_from_oss(
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
                object_path=OssFetcher.SPEED_PRO_TRAINER)
        if df_speed_pro_jockey.empty or df_speed_pro_trainer.empty:
            return None
        if run_top4:
            df_speed_pro_jockey = df_speed_pro_jockey.rename(columns={"top4_percent": "speed_pro_jockey_win_percent",
                                                                      "speedpro_category": "speed_pro_category"})
            df_speed_pro_trainer = df_speed_pro_trainer.rename(columns={"top4_percent": "speed_pro_trainer_win_percent",
                                                                        "speedpro_category": "speed_pro_category"})
        else:
            df_speed_pro_jockey = df_speed_pro_jockey.rename(columns={"win_percent": "speed_pro_jockey_win_percent",
                                                                      "speedpro_category": "speed_pro_category"})
            df_speed_pro_trainer = df_speed_pro_trainer.rename(columns={"win_percent": "speed_pro_trainer_win_percent",
                                                                        "speedpro_category": "speed_pro_category"})
        return df_speed_pro_jockey, df_speed_pro_trainer

    @classmethod
    def get_cold_door_jt_df(cls, run_top4: bool) -> pd.DataFrame():
        if run_top4:
            df_cold_door_jockey = OssFetcher.get_df_from_oss(
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
                object_path=OssFetcher.COLD_DOOR_JOCKEY_TOP4)
            df_cold_door_trainer = OssFetcher.get_df_from_oss(
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
                object_path=OssFetcher.COLD_DOOR_TRAINER_TOP4)
        else:
            df_cold_door_jockey = OssFetcher.get_df_from_oss(
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
                object_path=OssFetcher.COLD_DOOR_JOCKEY)
            df_cold_door_trainer = OssFetcher.get_df_from_oss(
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
                object_path=OssFetcher.COLD_DOOR_TRAINER)
        if df_cold_door_jockey.empty or df_cold_door_trainer.empty:
            return None

        if run_top4:
            df_cold_door_jockey = df_cold_door_jockey.rename(columns={"top4_percent": "cold_door_jockey_win_percent",
                                                                      "score": "cold_door_rating"})
            df_cold_door_trainer = df_cold_door_trainer.rename(columns={"top4_percent": "cold_door_trainer_win_percent",
                                                                        "score": "cold_door_rating"})
        else:
            df_cold_door_jockey = df_cold_door_jockey.rename(columns={"win_percent": "cold_door_jockey_win_percent",
                                                                      "score": "cold_door_rating"})
            df_cold_door_trainer = df_cold_door_trainer.rename(columns={"win_percent": "cold_door_trainer_win_percent",
                                                                        "score": "cold_door_rating"})
        return df_cold_door_jockey, df_cold_door_trainer

    @classmethod
    def get_fitness_jt_df(cls, run_top4: bool) -> pd.DataFrame():
        if run_top4:
            df_fitness_jockey = OssFetcher.get_df_from_oss(
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
                object_path=OssFetcher.FITNESS_RATINGS_JOCKEY_TOP4)
            df_fitness_trainer = OssFetcher.get_df_from_oss(
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
                object_path=OssFetcher.FITNESS_RATINGS_TRAINER_TOP4)
        else:
            df_fitness_jockey = OssFetcher.get_df_from_oss(
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
                object_path=OssFetcher.FITNESS_RATINGS_JOCKEY)
            df_fitness_trainer = OssFetcher.get_df_from_oss(
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
                object_path=OssFetcher.FITNESS_RATINGS_TRAINER)
        if df_fitness_jockey.empty or df_fitness_trainer.empty:
            return None
        if run_top4:
            df_fitness_jockey = df_fitness_jockey.rename(columns={"top4_percent": "fitness_ratings_jockey_win_percent"})
            df_fitness_trainer = df_fitness_trainer.rename(
                columns={"top4_percent": "fitness_ratings_trainer_win_percent"})
        else:
            df_fitness_jockey = df_fitness_jockey.rename(columns={"win_percent": "fitness_ratings_jockey_win_percent"})
            df_fitness_trainer = df_fitness_trainer.rename(
                columns={"win_percent": "fitness_ratings_trainer_win_percent"})
        return df_fitness_jockey, df_fitness_trainer

    @classmethod
    def get_wi_dict(cls) -> dict:
        win_investment_dict = OssFetcher.get_json_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path=OssFetcher.INVESTMENT_DIFFERENCE_CI)
        if win_investment_dict is None:
            logger.error("Failed to get win investment dict")
            return {}
        return win_investment_dict

    @classmethod
    def get_wi_snapshot_df(cls, minute_snapshot: int) -> pd.DataFrame():
        df_win_investment_snapshot = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_FEATURE_STORE,
            object_path=OssFetcher.INVESTMENT_SNAPSHOT)
        if df_win_investment_snapshot.empty:
            logger.error("Failed to get win investment snapshot")
            return None
        if minute_snapshot < 3:
            selected_column = f"{-(minute_snapshot + 1)}"
            df_win_investment_snapshot["is_invested"] = df_win_investment_snapshot[selected_column].apply(
                lambda x: True if x > 0 else False)
        else:
            df_win_investment_snapshot["is_invested"] = False

        df_win_investment_snapshot = df_win_investment_snapshot[["race_date", "race_num", "horse_num", "is_invested"]]
        return df_win_investment_snapshot

    @classmethod
    def get_wi_snapshot_df_jt_percent(cls, minute_snapshot: int, run_top4: bool) -> pd.DataFrame():
        df_win_investment_snapshot_jockey = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path=OssFetcher.INVESTMENT_DIFFERENCE_JOCKEY)
        df_win_investment_snapshot_trainer = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path=OssFetcher.INVESTMENT_DIFFERENCE_TRAINER)
        if df_win_investment_snapshot_jockey.empty or df_win_investment_snapshot_trainer.empty:
            logger.error("Failed to get win investment snapshot jockey or trainer")
            return None
        df_win_investment_snapshot_jockey = df_win_investment_snapshot_jockey[
            df_win_investment_snapshot_jockey["time_diff"] == minute_snapshot]

        df_win_investment_snapshot_trainer = df_win_investment_snapshot_trainer[
            df_win_investment_snapshot_trainer["time_diff"] == minute_snapshot]

        if run_top4:
            df_win_investment_snapshot_jockey["win_percent"] = (df_win_investment_snapshot_jockey["win"] +
                                                                df_win_investment_snapshot_jockey["top2-4"]) / \
                                                               (df_win_investment_snapshot_jockey["win"] +
                                                                df_win_investment_snapshot_jockey["top2-4"] +
                                                                df_win_investment_snapshot_jockey["lose"])
            df_win_investment_snapshot_trainer["win_percent"] = (df_win_investment_snapshot_trainer["win"] +
                                                                 df_win_investment_snapshot_trainer["top2-4"]) / \
                                                                (df_win_investment_snapshot_trainer["win"] +
                                                                 df_win_investment_snapshot_trainer["top2-4"] +
                                                                 df_win_investment_snapshot_trainer["lose"])

        df_win_investment_snapshot_jockey = df_win_investment_snapshot_jockey[
            ['jockey_code', 'win_odds_category', 'is_invested', "win_percent"]].rename(
            columns={"win_percent": "jockey_win_snapshot_percent"})

        df_win_investment_snapshot_trainer = df_win_investment_snapshot_trainer[
            ['trainer_code', 'win_odds_category', 'is_invested', "win_percent"]].rename(
            columns={"win_percent": "trainer_win_snapshot_percent"})
        return df_win_investment_snapshot_jockey, df_win_investment_snapshot_trainer

    @classmethod
    def get_ob_dict(cls, run_top4: bool) -> dict:
        if run_top4:
            overbought_dict = OssFetcher.get_json_from_oss(
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
                object_path=OssFetcher.OVERBOUGHT_CI_TOP4)
        else:
            overbought_dict = OssFetcher.get_json_from_oss(
                object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
                object_path=OssFetcher.OVERBOUGHT_CI)
        if overbought_dict is None:
            logger.error("Failed to get overbought dict")
            return {}
        return overbought_dict

    @classmethod
    def get_grouping_dict(cls, ci_dict: dict, jockey: str, trainer: str, win_cat: int, ci: int) -> dict:
        # Jockey
        jockey_dict = ci_dict.get("jockeys", {}).get(jockey, {})
        win_jockey = None
        if jockey_dict:
            win_jockey = jockey_dict.get(str(win_cat), {})
        jockey_dict = cls.create_response_body_dict_from_ci_dict(ci, win_jockey)
        # Trainer
        trainer_dict = ci_dict.get("trainers", {}).get(trainer, {})
        win_trainer = None
        if trainer_dict:
            win_trainer = trainer_dict.get(str(win_cat), {})
        trainer_dict = cls.create_response_body_dict_from_ci_dict(ci, win_trainer)
        return [jockey_dict, trainer_dict]

    @classmethod
    def create_response_body_dict_from_ci_dict(cls, ci: int, ci_dict: dict) -> dict:
        # Default response body
        response_body = {
            "within_range": False,
            "win_percentage_group": 0,
            "win_percentage": 0
        }
        if not ci or not ci_dict:
            return response_body
        # Get ci boundaries and win percentages from ci_dict
        ci_boundaries = ci_dict.get("ci_boundaries", [])
        win_percentages = ci_dict.get("win_percentages", [])
        if not ci_boundaries or not win_percentages:
            logger.debug("Invalid ci_dict format")
            return response_body
        # Check if ci is within range
        if ci_boundaries[0] >= ci >= ci_boundaries[-1]:
            for i in range(len(ci_boundaries) - 1):
                # Find range that ci falls into
                if ci_boundaries[i] >= ci >= ci_boundaries[i + 1]:
                    win_percentage = win_percentages[i]
                    # Sort win percentages in descending order, return index + 1 as win percentage group
                    win_percentages.sort(reverse=True)
                    response_body["win_percentage_group"] = win_percentages.index(
                        win_percentage) + 1
                    response_body["win_percentage"] = win_percentage
                    response_body["within_range"] = True
                    break
        return response_body

    @classmethod
    def separate_column(cls, df: pd.DataFrame, column: str) -> None:
        df[[f'jockey_{column}_tier', f'jockey_{column}_win_percentage',
            f'trainer_{column}_tier', f'trainer_{column}_win_percentage']] = df[f'{column}_tier'].apply(
            lambda x: (
                x[0]['win_percentage_group'], x[0]['win_percentage'], x[1]['win_percentage_group'],
                x[1]['win_percentage'])
        ).apply(pd.Series)
        df.fillna({f'jockey_{column}_tier': 0, f'jockey_{column}_win_percentage': 0,
                   f'trainer_{column}_tier': 0, f'trainer_{column}_win_percentage': 0}, inplace=True)

    @classmethod
    def get_decision_tree_df(cls) -> pd.DataFrame():
        df_decision_tree = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path=OssFetcher.DECISION_TREE)
        if df_decision_tree.empty:
            logger.error("Failed to get speed pro")
            return pd.DataFrame()
        df_decision_tree["reborn"] = df_decision_tree["reborn"].apply(
            lambda x: [] if x == '[]' else [int(i.strip()) for i in x.strip('[]').split(',')])
        df_decision_tree["deselected"] = df_decision_tree["deselected"].apply(
            lambda x: [] if x == '[]' else [int(i.strip()) for i in x.strip('[]').split(',')])
        return df_decision_tree

    @classmethod
    def get_dividend_from_response(cls, response: dict) -> List[float]:
        for field in ["win", "quinella", "tierce", "quartet"]:
            if not response.get(field, {}):
                logger.error(f"Failed to fetch {field} from payload")
                return []
        win = list(response['win'].values())[0] * 10
        quinella = response["quinella"][0].get('odds', 0) * 10
        tierce = response["tierce"][0].get('odds', 0) * 10
        quartet = response["quartet"][0].get('odds', 0) * 10
        place = response["place"]
        return [win, quinella, tierce, quartet, place]

    @classmethod
    def update_jt_tier(cls):
        jt_dict = OssFetcher.get_json_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path=OssFetcher.JT_TIER)
        if jt_dict is None:
            return None

        jockey_list = jt_dict.get("jockeys", [])
        jockey_filter_list = ["MOJ", "DSS", "BV"]
        trainer_list = jt_dict.get("trainers", [])
        if not jockey_list or not trainer_list:
            logger.error("Failed to get jockey or trainer list")
            return None
        result_jockey_list = [elem for elem in jockey_list if elem not in jockey_filter_list]
        cls.top_6_jockeys = result_jockey_list[0:6]
        cls.second_6_jockeys = result_jockey_list[6:12]
        cls.top_6_trainers = trainer_list[0:6]
        cls.second_6_trainers = trainer_list[6:12]
        logger.info(f"Updated Top jockey: {cls.top_6_jockeys, cls.second_6_jockeys}")
        logger.info(f"Updated Top trainer: {cls.top_6_trainers, cls.second_6_trainers}")

    @classmethod
    def get_contrast_df(cls) -> pd.DataFrame():
        df_contrast_jockey = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path="investment_contrast/evaluation_win_contrast_jockey_0min.csv")
        df_contrast_trainer = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path="investment_contrast/evaluation_win_contrast_trainer_0min.csv")

        if df_contrast_jockey.empty or df_contrast_trainer.empty:
            return None
        df_contrast_jockey = df_contrast_jockey[df_contrast_jockey["race_count"] >= 5]
        df_contrast_jockey = df_contrast_jockey[
            ["jockey_code", "hot", "invest_1_over_2_group", "hit_count", "race_count"]]
        df_contrast_jockey = df_contrast_jockey.rename(columns={"hit_count": "jockey_contrast_win",
                                                                "race_count": "jockey_contrast_count"})

        df_contrast_trainer = df_contrast_trainer[df_contrast_trainer["race_count"] >= 5].drop("percent", axis=1)
        df_contrast_trainer = df_contrast_trainer[
            ["trainer_code", "hot", "invest_1_over_2_group", "hit_count", "race_count"]]
        df_contrast_trainer = df_contrast_trainer.rename(columns={"hit_count": "trainer_contrast_win",
                                                                  "race_count": "trainer_contrast_count"})
        df_contrast_jockey.to_csv("jockey_contrast.csv", index=False)
        df_contrast_trainer.to_csv("trainer_contrast.csv", index=False)

    @classmethod
    def get_diff_df(cls) -> pd.DataFrame():
        df_contrast_trainer = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path="win_contrast/ratio_trainer_top1_1.csv")
        if df_contrast_trainer.empty:
            return None
        df_contrast_trainer = df_contrast_trainer[df_contrast_trainer["race_count"] >= 4].drop("percent", axis=1)
        df_contrast_trainer = df_contrast_trainer.rename(columns={"hit_count": "trainer_dd_win",
                                                                  "race_count": "trainer_dd_count",
                                                                  "percentage": "trainer_dd_percentage"})
        df_contrast_trainer["trainer_dd_percentage_group"] = df_contrast_trainer["trainer_dd_percentage"].apply(
            lambda x: 1 if x <= 0.15 else 2 if x <= 0.3 else 3)

        df_contrast_trainer.to_csv("trainer_dd.csv", index=False)

    @classmethod
    def get_expected_ci_df(cls) -> pd.DataFrame():
        df_expected_ci_jockey = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path="expected_ci/expected_ci_jockey_0min.csv")
        df_expected_ci_trainer = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path="expected_ci/expected_ci_trainer_0min.csv")
        if df_expected_ci_jockey.empty or df_expected_ci_trainer.empty:
            return None
        df_expected_ci_jockey = df_expected_ci_jockey[df_expected_ci_jockey["race_count"] >= 5]
        df_expected_ci_jockey = df_expected_ci_jockey[
            ["jockey_code", "is_overbought", "ci_group", "hit_count", "race_count"]]
        df_expected_ci_jockey = df_expected_ci_jockey.rename(columns={"hit_count": "jockey_expected_ci_win",
                                                                      "race_count": "jockey_expected_ci_count"})

        df_expected_ci_trainer = df_expected_ci_trainer[df_expected_ci_trainer["race_count"] >= 5]
        df_expected_ci_trainer = df_expected_ci_trainer[
            ["trainer_code", "is_overbought", "ci_group", "hit_count", "race_count"]]
        df_expected_ci_trainer = df_expected_ci_trainer.rename(columns={"hit_count": "trainer_expected_ci_win",
                                                                        "race_count": "trainer_expected_ci_count"})

        df_expected_ci_jockey.to_csv("jockey_expected_ci.csv", index=False)
        df_expected_ci_trainer.to_csv("trainer_expected_ci.csv", index=False)
    @classmethod
    def get_expected_qw_df(cls) -> pd.DataFrame():
        df_expected_qw_jockey = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path="expected_qw/expected_qw_jockey_0min.csv")
        df_expected_qw_trainer = OssFetcher.get_df_from_oss(
            object_bucket=OssFetcher.BUCKET_READ_LAKEHOUSE,
            object_path="expected_qw/expected_qw_trainer_0min.csv")
        if df_expected_qw_jockey.empty or df_expected_qw_trainer.empty:
            return None
        df_expected_qw_jockey = df_expected_qw_jockey[df_expected_qw_jockey["race_count"] >= 5]
        df_expected_qw_jockey = df_expected_qw_jockey[
            ["jockey_code", "win_odds_category", "qw_group", "hit_count", "race_count"]]
        df_expected_qw_jockey = df_expected_qw_jockey.rename(columns={"hit_count": "jockey_expected_qw_win",
                                                                      "race_count": "jockey_expected_qw_count"})

        df_expected_qw_trainer = df_expected_qw_trainer[df_expected_qw_trainer["race_count"] >= 5]
        df_expected_qw_trainer = df_expected_qw_trainer[
            ["trainer_code", "win_odds_category", "qw_group", "hit_count", "race_count"]]
        df_expected_qw_trainer = df_expected_qw_trainer.rename(columns={"hit_count": "trainer_expected_qw_win",
                                                                        "race_count": "trainer_expected_qw_count"})

        df_expected_qw_jockey.to_csv("jockey_expected_qw.csv", index=False)
        df_expected_qw_trainer.to_csv("trainer_expected_qw.csv", index=False)
