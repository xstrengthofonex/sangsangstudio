from abc import ABC, abstractmethod
from datetime import datetime
from zoneinfo import ZoneInfo


class Clock(ABC):
    @abstractmethod
    def now(self) -> datetime:
        pass

    @abstractmethod
    def add_timezone(self, dt: datetime) -> datetime:
        pass

    @classmethod
    @abstractmethod
    def default_timezone(cls) -> str:
        pass


class SystemClock(Clock):
    DEFAULT_TIMEZONE = "Asia/Seoul"

    def __init__(self, time_zone: str = ""):
        self.tz_info = ZoneInfo(time_zone or self.DEFAULT_TIMEZONE)

    def now(self) -> datetime:
        return datetime.now(self.tz_info)

    def add_timezone(self, dt: datetime) -> datetime:
        return dt.replace(tzinfo=self.tz_info)

    @classmethod
    def default_timezone(cls) -> ZoneInfo:
        return ZoneInfo(cls.DEFAULT_TIMEZONE)
