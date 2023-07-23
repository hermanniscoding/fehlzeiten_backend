import enum

class SchoolyearEnum(enum.Enum):
    E1 = 'E1'
    E2 = 'E2'
    E3 = 'E3'
    S3 = 'S3'
    S4 = 'S4'

class GroupEnum(enum.Enum):
    A1 = 'A1'
    A2 = 'A2'
    A3 = 'A3'
    B1 = 'B1'
    B2 = 'B2'
    B3 = 'B3'
    B4 = 'B4'
    C1 = 'C1'
    C2 = 'C2'
    C3 = 'C3'

class MissedTypeEnum(enum.Enum):
    missed = 'missed'
    late = 'late'
    distance = 'distance'

class AdmonitionTypeEnum(enum.Enum):
    yellow = 'yellow'
    red = 'red'

class SubjectTypeEnum(enum.Enum):
    deutsch = 'deutsch'
    mathe = 'mathe'
    englisch = 'englisch'
    projekt = 'projekt'
    kunst = 'kunst'
    sonstiges = 'sonstiges'
subject_enums = [member.value for member in SubjectTypeEnum]
