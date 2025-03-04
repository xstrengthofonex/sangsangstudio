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

class SystemClock(Clock):
    def __init__(self, time_zone: str = "Asia/Seoul"):
        self.tz_info = ZoneInfo(time_zone)

    def now(self) -> datetime:
        return datetime.now(self.tz_info)

    def add_timezone(self, dt: datetime) -> datetime:
        return dt.replace(tzinfo=self.tz_info)
