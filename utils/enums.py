from enum import Enum, unique


@unique
class FileExtension(Enum):
    CSV = ".csv"
    TSV = ".tsv"
    TXT = ".txt"
    JSON = ".json"

    @classmethod
    def parse(cls, s: str):
        return cls[s.lstrip(".").upper()]


@unique
class FileSeperator(Enum):
    CSV = ","
    TSV = "\t"


@unique
class TermType(Enum):
    TEXT = 0
    FONT = 1
    TEXTURE = 2
    AUDIO_CLIP = 3
    GAME_OBJECT = 4
    SPRITE = 5
    MATERIAL = 6
    CHILD = 7
    MESH = 8
    OBJECT = 9
    VIDEO = 10

    @property
    def displayed(self):
        return self.name.title().strip().replace("_", " ")

    @classmethod
    def parse(cls, s: str):
        return cls[s.replace(" ", "_").upper()]

    @classmethod
    def get_value(cls, s: str | Enum):
        return cls.parse(s).value if isinstance(s, str) else s.value

    @classmethod
    def titles(cls):
        return [e.displayed for e in cls]


@unique
class PluralType(Enum):
    ZERO = 0
    ONE = 1
    TWO = 2
    FEW = 3
    MANY = 4
    PLURAL = 5


@unique
class LanguageDataFlags(Enum):
    ENABLED = 0
    DISABLED = 1

    @property
    def displayed(self):
        return self.name.title()

    @classmethod
    def parse(cls, s: str):
        return cls[s.upper()]

    @classmethod
    def get_value(cls, s: str | Enum):
        return cls.parse(s).value if isinstance(s, str) else s.value

    @classmethod
    def titles(cls):
        return [e.displayed for e in cls]


@unique
class MissingTranslationAction(Enum):
    EMPTY = 0
    FALLBACK = 1
    SHOW_WARNING = 2
    SHOW_TERM = 3

    @property
    def displayed(self):
        return self.name.title().replace("_", " ")

    @classmethod
    def parse(cls, s: str):
        return cls[s.replace(" ", "_").upper()]

    @classmethod
    def get_value(cls, s: str | Enum):
        return cls.parse(s).value if isinstance(s, str) else s.value

    @classmethod
    def titles(cls):
        return [e.displayed for e in cls]


class AllowUnloadLanguages(Enum):
    NEVER = 0
    ONLY_IN_DEVICE = 1
    EDITOR_AND_DEVICE = 2

    @property
    def displayed(self):
        return self.name.title().replace("_", " ")

    @classmethod
    def parse(cls, s: str):
        return cls[s.replace(" ", "_").upper()]

    @classmethod
    def get_value(cls, s: str | Enum):
        return cls.parse(s).value if isinstance(s, str) else s.value

    @classmethod
    def titles(cls):
        return [e.displayed for e in cls]


@unique
class GoogleUpdateFrequency(Enum):
    ALWAYS = 0
    NEVER = 1
    DAILY = 2
    WEEKLY = 3
    MONTHLY = 4
    ONLY_ONCE = 5
    EVERY_OTHER_DAY = 6

    @property
    def displayed(self):
        return self.name.title().replace("_", " ")

    @classmethod
    def parse(cls, s: str):
        return cls[s.replace(" ", "_").upper()]

    @classmethod
    def get_value(cls, s: str | Enum):
        return cls.parse(s).value if isinstance(s, str) else s.value

    @classmethod
    def titles(cls):
        return [e.displayed for e in cls]


@unique
class GoogleUpdateSynchronization(Enum):
    MANUAL = 0
    ON_SCENE_LOADED = 1
    AS_SOON_AS_DOWNLOADED = 2

    @property
    def displayed(self):
        return self.name.title().replace("_", " ")

    @classmethod
    def parse(cls, s: str):
        return cls[s.replace(" ", "_").upper()]

    @classmethod
    def get_value(cls, s: str | Enum):
        return cls.parse(s).value if isinstance(s, str) else s.value

    @classmethod
    def titles(cls):
        return [e.displayed for e in cls]
