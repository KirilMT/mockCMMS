import sys


class FakeNotification:
    def notify(self, **kwargs):
        pass


class FakePlyer:
    notification = FakeNotification()


sys.modules["plyer"] = FakePlyer()  # type: ignore[assignment]
