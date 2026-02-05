from enum import Enum, EnumMeta, unique

from utils.app_locales import ftr


class CustomEnumMeta(EnumMeta):
    def __getitem__(cls, name: str | Enum):
        if isinstance(name, str):
            try:
                return super().__getitem__(name.replace(" ", "_").upper())
            except KeyError:
                return None
        elif isinstance(name, Enum):
            return name.value
        return None


class CustomEnum(Enum, metaclass=CustomEnumMeta):
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
    def titles(cls, prefix: str = ""):
        if prefix:
            return [ftr(f"{prefix}-{e.displayed.lower()}") for e in cls]
        return [e.displayed for e in cls]


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
class TermType(CustomEnum):
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


@unique
class PluralType(CustomEnum):
    ZERO = 0
    ONE = 1
    TWO = 2
    FEW = 3
    MANY = 4
    PLURAL = 5


@unique
class LanguageDataFlags(CustomEnum):
    ENABLED = 0
    DISABLED = 1


@unique
class MissingTranslationAction(CustomEnum):
    EMPTY = 0
    FALLBACK = 1
    SHOW_WARNING = 2
    SHOW_TERM = 3


class AllowUnloadLanguages(CustomEnum):
    NEVER = 0
    ONLY_IN_DEVICE = 1
    EDITOR_AND_DEVICE = 2


@unique
class GoogleUpdateFrequency(CustomEnum):
    ALWAYS = 0
    NEVER = 1
    DAILY = 2
    WEEKLY = 3
    MONTHLY = 4
    ONLY_ONCE = 5
    EVERY_OTHER_DAY = 6


@unique
class GoogleUpdateSynchronization(CustomEnum):
    MANUAL = 0
    ON_SCENE_LOADED = 1
    AS_SOON_AS_DOWNLOADED = 2

