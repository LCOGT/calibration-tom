from enum import Enum, unique


@unique
class InstrumentState(Enum):
    DISABLED = 'DISABLED'
    MANUAL = 'MANUAL'
    COMMISSIONING = 'COMMISSIONING'
    STANDBY = 'STANDBY'
    SCHEDULABLE = 'SCHEDULABLE'
    ENABLED = 'ENABLED'

    def __gt__(self, o: Enum) -> bool:
        if not isinstance(o, InstrumentState):
            return NotImplemented

        return self.value > o.value

    def __lt__(self, o: Enum) -> bool:
        if not isinstance(o, InstrumentState):
            return NotImplemented

        return self.value < o.value
