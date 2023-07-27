import enum

class MissedTypeEnum(enum.Enum):
    missed = 'missed'
    late = 'late'
    distance = 'distance'
    home = 'home'

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
