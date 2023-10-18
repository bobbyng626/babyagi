import oss2
from oss2.exceptions import RequestError
import pandas as pd
from settings import SETTINGS
from io import BytesIO
from typing import Union
from aexlutils import logger
import json


class OssFetcher:
    OSS_ACCESS_KEY_ID = SETTINGS.OSS.access_key_id
    OSS_ACCESS_KEY_SECRET = SETTINGS.OSS.access_key_secret
    OSS_ENDPOINT = "https://oss-cn-hongkong.aliyuncs.com"
    OSS_AUTH = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
    
    OSS_EVENT_STORE_BUCKET_NAME = 'aexl-hkjc-oss'
    OSS_FEATURE_STORE_BUCKET_NAME = 'aexl-hkjc-feature-store'
    OSS_EVENT_STORE_BUCKET = oss2.Bucket(OSS_AUTH, OSS_ENDPOINT, OSS_EVENT_STORE_BUCKET_NAME)
    OSS_FEATURE_STORE_BUCKET = oss2.Bucket(OSS_AUTH, OSS_ENDPOINT, OSS_FEATURE_STORE_BUCKET_NAME)

    # Feature store
    OSS_BUCKET_NAME_FEATURE_STORE = 'aexl-hkjc-feature-store'
    BUCKET_READ_FEATURE_STORE = oss2.Bucket(
        auth=OSS_AUTH,
        endpoint=OSS_ENDPOINT,
        bucket_name=OSS_BUCKET_NAME_FEATURE_STORE)

    # Lakehouse
    OSS_BUCKET_NAME_LAKEHOUSE = 'aexl-jc-lakehouse'
    BUCKET_READ_LAKEHOUSE = oss2.Bucket(
        auth=OSS_AUTH,
        endpoint=OSS_ENDPOINT,
        bucket_name=OSS_BUCKET_NAME_LAKEHOUSE)

    # JC Lakehouse
    # Win
    INVESTMENT_DIFFERENCE_CI = "statistics-service/investment-difference/investment_difference_statistics.json"
    INVESTMENT_DIFFERENCE_JOCKEY = "statistics-service/investment-difference/investment_difference_snapshot_jockey.csv"
    INVESTMENT_DIFFERENCE_TRAINER = "statistics-service/investment-difference/investment_difference_snapshot_trainer.csv"
    JT_TIER = "statistics-service/jockey-trainer-ranking/jockey_trainer_ranking.json"
    OVERBOUGHT_CI = "statistics-service/overbought/overbought_ci_statistics.json"
    SPEED_PRO_JOCKEY = "statistics-service/speedpro/speedpro_jockey.csv"
    SPEED_PRO_TRAINER = "statistics-service/speedpro/speedpro_trainer.csv"
    COLD_DOOR_JOCKEY = "statistics-service/cold-door/cold_door_jockey.csv"
    COLD_DOOR_TRAINER = "statistics-service/cold-door/cold_door_trainer.csv"
    FITNESS_RATINGS_JOCKEY = "statistics-service/fitness-ratings/fitness_ratings_jockey.csv"
    FITNESS_RATINGS_TRAINER = "statistics-service/fitness-ratings/fitness_ratings_trainer.csv"
    JOCKEY_GAIN = "statistics-service/jt-gains/jockey_gains.csv"
    TRAINER_GAIN = "statistics-service/jt-gains/trainer_gains.csv"
    DECISION_TREE = "past_decision_tree/past_decision_tree.csv"
    # Top4
    INVESTMENT_DIFFERENCE_JOCKEY_TOP4 = "statistics-service/investment-difference/investment_difference_snapshot_jockey_top4.csv"
    INVESTMENT_DIFFERENCE_TRAINER_TOP4 = "statistics-service/investment-difference/investment_difference_snapshot_trainer_top4.csv"
    OVERBOUGHT_CI_TOP4 = "statistics-service/overbought/overbought_ci_statistics_top4.json"
    SPEED_PRO_JOCKEY_TOP4 = "statistics-service/speedpro/speedpro_jockey_top4.csv"
    SPEED_PRO_TRAINER_TOP4 = "statistics-service/speedpro/speedpro_trainer_top4.csv"
    COLD_DOOR_JOCKEY_TOP4 = "statistics-service/cold-door/cold_door_jockey_top4.csv"
    COLD_DOOR_TRAINER_TOP4 = "statistics-service/cold-door/cold_door_trainer_top4.csv"
    FITNESS_RATINGS_JOCKEY_TOP4 = "statistics-service/fitness-ratings/fitness_ratings_jockey_top4.csv"
    FITNESS_RATINGS_TRAINER_TOP4 = "statistics-service/fitness-ratings/fitness_ratings_trainer_top4.csv"
    JT_TIER_TOP4 = "statistics-service/jockey-trainer-ranking/jockey_trainer_ranking_top4.json"

    # Feature store
    # Win
    INVESTMENT_SNAPSHOT = "statistics_service_data/investment_difference_count_by_snapshot.parquet"
    PAST_PERFORMANCE = "statistics_service_data/past_performance.parquet"
    TRAINER_PERFORMANCE = "statistics_service_data/trainer_performance.csv"
    JOCKEY_PERFORMANCE = "statistics_service_data/jockey_performance.csv"
    SPEED_PRO = "event_store_parquet/speedpro.parquet"
    COLD_DOOR = "event_store_parquet/cold_door.parquet"
    DIVIDEND = "event_store_parquet/dividends.json"

    @classmethod
    def get_df_from_oss(cls, object_bucket, object_path: str) -> pd.DataFrame:
        # Exception handling
        if not object_bucket:
            return pd.DataFrame()
        if not object_bucket.object_exists(key=object_path):
            logger.error(f"Past Performance object does not exist in OSS bucket, skipping.")
            return pd.DataFrame()

        # Query Oss
        for attempt in range(1, 4):
            try:
                result = object_bucket.get_object(key=object_path).read()
            except RequestError as e:
                logger.error(f"Request error. Retrying {attempt} time. Error message: {e}")
            else:
                break
        else:
            logger.error(f"Connection failed from bucket: {object_bucket}, path: {object_path}")
            return pd.DataFrame()

        # Empty file exception
        if len(result) == 0:
            logger.error(f"Obtained empty object. Path: {object_path}")
            return pd.DataFrame()

        logger.info(f"Obtained object: {object_path}")
        if object_path.endswith(".parquet"):
            return pd.read_parquet(BytesIO(result))
        if object_path.endswith(".csv"):
            return pd.read_csv(BytesIO(result))
        return pd.DataFrame()

    @classmethod
    def get_json_from_oss(cls, object_bucket: str, object_path: str) -> dict:
        # Exception handling
        if not object_bucket:
            return {}
        if not object_bucket.object_exists(key=object_path):
            logger.error(f"Past Performance object does not exist in OSS bucket, skipping.")
            return {}

        # Query Oss
        for attempt in range(1, 4):
            try:
                # Read object
                result = object_bucket.get_object(key=object_path).read()
            except RequestError as e:
                logger.error(f"Request error. Retrying {attempt} time. Error message: {e}")
            else:
                break
        else:
            logger.error(f"Connection failed from bucket: {object_bucket}, path: {object_path}")
            return {}

        # Empty file exception
        if len(result) == 0:
            logger.error(f"Obtained empty object. Path: {object_path}")
            return {}

        return json.loads(result)

    @classmethod
    def put_df_as_csv_to_bucket(cls, df: pd.DataFrame(), race_date_string: str, object_bucket: str):
        buffer = BytesIO()
        file_name = f"llm_result/{race_date_string}_result.csv"
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        object_bucket.put_object(f"{file_name}", buffer.getvalue())
        logger.info(f"Put data into {object_bucket}")

    @classmethod
    def put_json_to_bucket(cls, df: pd.DataFrame(), race_date_string: str, object_bucket: str):
        buffer = BytesIO()
        file_name = f"{race_date_string}_result.csv"
        df.to_json(buffer, index=False)
        buffer.seek(0)
        object_bucket.put_object(f"llm_result/{file_name}", buffer.getvalue())
        logger.info(f"Put data into {object_bucket}/llm_result")

    @classmethod
    def get_roadmap_result_df(cls) -> pd.DataFrame():
        object_list = []
        for obj in oss2.ObjectIterator(cls.BUCKET_READ_LAKEHOUSE, prefix="llm_result"):
            object_list.append(obj.key)

        dfs = []
        for obj_key in object_list:
            df = cls.get_df_from_oss(object_bucket=cls.BUCKET_READ_LAKEHOUSE,
                                     object_path=f"llm_result/{obj_key.split('/')[-1]}")
            dfs.append(df)

        df_result = pd.concat(dfs).reset_index(drop=True)
        df_result = df_result.sort_values(by=['raceDate', 'raceNum', 'min'])
        df_result = df_result.rename(columns={
            "raceDate": "race_date",
            "raceNum": "race_num",
        })
        df_result = df_result[["race_date", "race_num", "min", "roadmapRanking"]]
        logger.info(f"Obtained roadmap result dataframe")
        return df_result

    @classmethod
    def read_json_from_event_store(cls, object_path: str, return_last_item: bool = True) -> Union[dict, None]:
        try:
            obj = json.loads(cls.OSS_EVENT_STORE_BUCKET.get_object(object_path).read().decode('utf-8'))
            return obj[-1] if return_last_item else obj
        except oss2.exceptions.NoSuchKey:
            return None

    @classmethod
    def get_paths_of_all_objects_in_directory_from_event_store(cls, directory_path: str) -> list:
        object_paths_details = oss2.ObjectIterator(cls.OSS_EVENT_STORE_BUCKET, prefix=directory_path)
        return [obj.key for obj in object_paths_details]

    @classmethod
    def read_parquet_from_feature_store(cls, object_path: str) -> Union[pd.DataFrame, None]:
        try:
            obj = cls.OSS_FEATURE_STORE_BUCKET.get_object(object_path).read()
            df = pd.read_parquet(BytesIO(obj))
            return df
        except oss2.exceptions.NoSuchKey:
            return None
