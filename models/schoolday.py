from copy import error
import enum
from flask_sqlalchemy import SQLAlchemy
from .pupil import *
from .enums import *

db = SQLAlchemy()



#- ##############################################################################################
#################################################################################################
#-     SCHOOLDAY    ##################################################################################
#################################################################################################
#- ##############################################################################################


class Schoolday(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    schoolday = db.Column(db.Date, nullable = False)
    
    #- RELATIONSHIPS ONE-TO-MANY
    missedclasses = db.relationship('MissedClass', back_populates='missed_day', cascade="all, delete-orphan")
    admonitions = db.relationship('Admonition', back_populates='admonished_day', cascade="all, delete-orphan")

    def __init__(self, schoolday):
        self.schoolday = schoolday    

#- ######################################################################################################
#########################################################################################################
#-     MISSED CLASS    ##################################################################################
#########################################################################################################
#- ######################################################################################################
  

class MissedClass(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    missed_type = db.Column(db.Enum(MissedTypeEnum), nullable = False)
    excused = db.Column(db.Boolean)
    contacted = db.Column(db.Boolean)
    returned = db.Column(db.Boolean)
    written_excuse = db.Column(db.Boolean)
    late_at = db.Column(db.String(5), nullable=True)
    returned_at = db.Column(db.String(5), nullable=True)
    created_by = db.Column(db.String(20), nullable=True)
    modified_by = db.Column(db.String(20), nullable=True)

    #- RELATIONSHIP TO PUPIL MANY-TO-ONE
    missed_pupil_id = db.Column(db.Integer, db.ForeignKey('pupil.internal_id'))
    missed_pupil = db.relationship('Pupil', back_populates='pupilmissedclasses')

    #- RELATIONSHIP TO SCHOOLDAY MANY-TO-ONE
    missed_day_id = db.Column(db.Integer, db.ForeignKey('schoolday.id'))
    missed_day = db.relationship('Schoolday', back_populates='missedclasses')
    
    def __init__(self, missed_pupil_id, missed_day_id, missed_type, excused, contacted, returned, written_excuse, late_at, returned_at, created_by, modified_by):
        self.missed_pupil_id = missed_pupil_id
        self.missed_day_id = missed_day_id
        self.missed_type = missed_type
        self.excused = excused
        self.contacted = contacted
        self.returned = returned
        self.written_excuse = written_excuse
        self.late_at = late_at
        self.returned_at = returned_at
        self.created_by = created_by
        self.modified_by = modified_by

#- ##############################################################################################
#################################################################################################
#-     ADMONITION     ##################################################################################
#################################################################################################
#- ##############################################################################################

## We need to document admonitions to monitor adequate educational measures
class Admonition(db.Model):
    id = db.Column(db.Integer, primary_key = True)   
    admonition_type = db.Column(db.Enum(AdmonitionTypeEnum),
    nullable = False)
    admonition_reason = db.Column(db.String(200), nullable = False)

    #- RELATIONSHIP TO PUPIL MANY-TO-ONE
    admonishedpupil_id = db.Column('admonished_pupil', db.Integer, db.ForeignKey('pupil.internal_id'))
    admonished_pupil = db.relationship('Pupil', back_populates="pupiladmonitions")
    
    #- RELATIONSHIP TO SCHOOLDAY MANY-TO-ONE
    admonished_day_id = db.Column('admonished_day', db.Integer, db.ForeignKey('schoolday.id'))
    admonished_day = db.relationship('Schoolday', back_populates="admonitions")

    def __init__(self, admonishedpupil_id, admonished_day_id, admonition_type, admonition_reason):
        self.admonishedpupil_id = admonishedpupil_id
        self.admonished_day_id = admonished_day_id
        self.admonition_type = admonition_type
        self.admonition_reason = admonition_reason


