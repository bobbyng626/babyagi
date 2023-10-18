class ChineseEnglishMapper:
    race_venue_dict = {
        "沙田": "Sha Tin",
        "跑馬地": "Happy Valley"
    }

    race_class_dict = {
        "第一班": "Class 1",
        "第二班": "Class 2",
        "第三班": "Class 3",
        "第四班": "Class 4",
        "第五班": "Class 5",
        "國際一級賽": "Group 1",
        "國際二級賽": "Group 2",
        "國際三級賽": "Group 3",
        "一級賽": "Group 1",
        "二級賽": "Group 2",
        "三級賽": "Group 3",
        "四歲": "4 Year Olds",
        "新馬賽": "Griffin"
    }

    race_class_num_dict = {
        "第一班": 1,
        "第二班": 2,
        "第三班": 3,
        "第四班": 4,
        "第五班": 5,
        "國際一級賽": 1,
        "國際二級賽": 1,
        "國際三級賽": 1,
        "一級賽": 1,
        "二級賽": 1,
        "三級賽": 1,
        "四歲": 1,
        "新馬賽": 5
    }

    race_track_dict = {
        "草地": "Turf",
        "全天候跑道": "All Weather Track"
    }

    race_track_condition_dict = {
        "快地": "Firm",
        "好地至快地": "Good to Firm",
        "好地": "Good",
        "好地至黏地": "Good to Yielding",
        "黏地": "Yielding",
        "濕慢地": "Wet Slow",
        "軟地": "Soft"
    }

    @classmethod
    def map_race_venue(cls, race_venue: str) -> str:
        if race_venue is None or len(race_venue) == 0:
            return ''
        return cls.race_venue_dict.get(race_venue, '')

    @classmethod
    def map_race_class(cls, race_class: str) -> str:
        if race_class is None or len(race_class) == 0:
            return ''
        if "（條件限制）" in race_class:
            race_class = race_class.split("（條件限制）")[0]
        return cls.race_class_dict.get(race_class, '')

    @classmethod
    def map_race_class_to_group(cls, race_class: str) -> int:
        if race_class is None or len(race_class) == 0:
            return 5
        if "（條件限制）" in race_class:
            race_class = race_class.split("（條件限制）")[0]
        return cls.race_class_num_dict.get(race_class, 5)

    @classmethod
    def map_race_track(cls, race_track: str) -> str:
        if race_track is None or len(race_track) == 0:
            return ''
        if "草地" in race_track:
            return cls.race_track_dict.get("草地", '')
        if "全天候" in race_track:
            return cls.race_track_dict.get("全天候跑道", '')
        return ''

    @classmethod
    def map_race_track_condition(cls, race_track_condition: str) -> str:
        if race_track_condition is None or len(race_track_condition) == 0:
            return ''
        return cls.race_track_condition_dict.get(race_track_condition, '')
