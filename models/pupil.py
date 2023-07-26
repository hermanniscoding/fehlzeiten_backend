from copy import error
from sqlalchemy.orm import backref, relationship
from sqlalchemy_utils import auto_delete_orphans
from .schoolday import *
from .enums import *

# db = SQLAlchemy()

#- ##############################################################################################
#################################################################################################
#-     PUPIL    ##################################################################################
#################################################################################################
#- ##############################################################################################

class Pupil(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    internal_id = db.Column(db.Integer, nullable=False, unique=True)
    credit = db.Column(db.Integer, default = 0)
    ogs = db.Column(db.Boolean)
    individual_development_plan = db.Column(db.Integer, default = 0)
    five_years = db.Column(db.String(2), nullable = True)
    special_needs = db.Column(db.String(8))
    communication_pupil = db.Column(db.String(8))
    communication_tutor1 = db.Column(db.String(8))
    communication_tutor2 = db.Column(db.String(8), nullable=True)
    preschool_revision = db.Column(db.Integer, default = 0)
    migration_support_ends = db.Column(db.Date, nullable = True)
    migration_follow_support_ends = db.Column(db.Date, nullable = True)
    avatar_url = db.Column(db.String(50), nullable = True)
    special_information = db.Column(db.String(200), nullable=True)

    #- RELATIONSHIPS
    #################

    #- RELATIONSHIPS ONE-TO-MANY
    pupilmissedclasses = db.relationship('MissedClass', back_populates='missed_pupil',
                                         cascade="all, delete-orphan")
    pupiladmonitions = db.relationship('Admonition', back_populates='admonished_pupil',
                                       cascade="all, delete-orphan")
    
    #- TO ASSOCIATION OBJECTS - TO-DO: IMPLEMENT DELETE ORPHAN
    pupilgoals = db.relationship('PupilGoal', back_populates='pupil',
                                 cascade="all, delete-orphan")
    pupilcategorystatuses = db.relationship('PupilCategoryStatus',
                                            back_populates='pupil',
                                            cascade="all, delete-orphan")
    pupilworkbooks = db.relationship('PupilWorkbook', back_populates='pupils',
                                      cascade="all, delete-orphan")
    pupillists = db.relationship('PupilList', back_populates='listed_pupil',
                                 cascade="all, delete-orphan")
    #- RELATIONSHIPS MANY TO ONE

    def __init__(self, internal_id, credit, ogs, individual_development_plan,
                 five_years, special_needs, communication_pupil, communication_tutor1,
                 communication_tutor2, preschool_revision, migration_support_ends,
                 migration_follow_support_ends, avatar_url, special_information):
        self.internal_id = internal_id
        self.credit = credit
        self.ogs = ogs
        self.individual_development_plan = individual_development_plan
        self.five_years = five_years
        self.special_needs = special_needs
        self.communication_pupil = communication_pupil
        self.communication_tutor1 = communication_tutor1
        self.communication_tutor2 = communication_tutor2
        self.preschool_revision = preschool_revision
        self.migration_support_ends = migration_support_ends
        self.migration_follow_support_ends = migration_follow_support_ends
        self.avatar_url = avatar_url
        self.special_information = special_information

#- ##############################################################################################
#################################################################################################
#-     WORKBOOK    ##############################################################################
#################################################################################################
#- ##############################################################################################

class Workbook(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    isbn = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(20))
    subject = db.Column(db.Enum(SubjectTypeEnum))

    #- RELATIONSHIPS ##################

    #- RELATIONSHIP TO PUPIL WORKBOOKS ONE-TO-MANY
    workbookpupils = db.relationship('PupilWorkbook', back_populates='workbook',
                                     cascade='all, delete-orphan')

    def __init__(self, isbn, name, subject):
        self.isbn = isbn
        self.name = name
        self.subject = subject
 
## many to many & association proxy: https://youtu.be/IlkVu_LWGys

class PupilWorkbook(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    state = db.Column(db.String(10), nullable = True)
    created_by = db.Column(db.String(20),nullable = False)
    created_at = db.Column(db.String(25), nullable = False)

    #- RELATIONSHIP TO PUPIL MANY-TO-ONE
    pupil_id = db.Column('pupil_id', db.Integer, db.ForeignKey('pupil.internal_id'))
    pupils = db.relationship('Pupil', back_populates='pupilworkbooks')

    #- RELATIONSHIP TO WORKBOOK MANY-TO-ONE
    workbook_isbn = db.Column('isbn_id', db.Integer, db.ForeignKey('workbook.isbn'))
    workbook = db.relationship('Workbook', back_populates='workbookpupils')

    def __init__(self, pupil_id, workbook_isbn, state, created_by, created_at):
        self.pupil_id = pupil_id
        self.workbook_isbn = workbook_isbn
        self.state = state
        self.created_by = created_by
        self.created_at = created_at

#- ##############################################################################################
#################################################################################################
#-     LISTS ####################################################################################
#################################################################################################
#- ##############################################################################################

class SchoolList(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    list_id = db.Column(db.Integer, nullable = False, unique = True)
    list_name = db.Column(db.String(20), nullable = False)
    list_description = db.Column(db.String(100), nullable=False)
    created_by = db.Column(db.String(5), nullable = False)

    #- RELATIONSHIPS #####################

    #- RELATIONSHIP TO PUPILS ONE-TO-MANY over PUPIL LIST
    pupilsinlist = db.relationship('PupilList', back_populates='pupil_in_list',
                                   cascade="all, delete-orphan")

    def __init__(self, list_id, list_name, list_description, created_by):
        self.list_id = list_id
        self.list_name = list_name
        self.list_description = list_description
        self.created_by = created_by

class PupilList(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    pupil_list_status = db.Column(db.Boolean)
    pupil_list_comment = db.Column(db.String(30))
    pupil_list_entry_by = db.Column(db.String(20))

    #- RELATIONSHIPS #######################################

    #- RELATIONSHIP TO SCHOOL LIST MANY-TO-ONE
    origin_list = db.Column(db.String(20), db.ForeignKey('school_list.list_id'))
    pupil_in_list = db.relationship('SchoolList', back_populates='pupilsinlist')

    #- RELATIONSHIP TO PUPIL MANY-TO-ONE
    listed_pupil_id = db.Column(db.Integer, db.ForeignKey('pupil.internal_id'))
    listed_pupil = db.relationship('Pupil', back_populates='pupillists')
    

    def __init__(self, origin_list, listed_pupil_id, pupil_list_status,
                 pupil_list_comment, pupil_list_entry_by):
        self.origin_list = origin_list
        self.listed_pupil_id = listed_pupil_id
        self.pupil_list_status = pupil_list_status
        self.pupil_list_comment = pupil_list_comment
        self.pupil_list_entry_by = pupil_list_entry_by    


#- ####################################
#######################################
#-      PUPIL GOALs ###################
#######################################
#- ####################################

class PupilCategoryStatus(db.Model):
    # id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(10), nullable = True)
    created_by = db.Column(db.String(20),nullable = False)
    created_at = db.Column(db.DateTime, nullable = False)

    #- RELATIONSHIP TO PUPIL MANY-TO-ONE
    ## Both foreign keys are primary keys because it can only be a category state for a pupil
    pupil_id = db.Column('pupil_id', db.Integer, db.ForeignKey('pupil.internal_id'), primary_key=True)
    pupil = db.relationship('Pupil', back_populates='pupilcategorystatuses')

    #- RELATIONSHIP TO CATEGORY MANY-TO-ONE
    goal_category_id = db.Column('goal_category_id', db.Integer,
                                 db.ForeignKey('goal_category.id'), primary_key=True)
    goal_category = db.relationship('GoalCategory', back_populates='categorystatuses')

    def __init__(self, pupil_id, goal_category_id, state, created_by, created_at):
        self.pupil_id = pupil_id
        self.goal_category_id = goal_category_id
        self.state = state
        self.created_by = created_by
        self.created_at = created_at

class PupilGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, nullable = False, unique = True)
    created_by = db.Column(db.String(20),nullable = False)
    created_at = db.Column(db.String(25), nullable = False)
    achieved = db.Column(db.Integer)
    achieved_at = db.Column(db.String(25), nullable = True)
    description = db.Column(db.String(200), nullable = False)
    strategies = db.Column(db.String(500))

    #- RELATIONSHIP TO PUPIL MANY-TO-ONE
    pupil_id = db.Column(db.Integer, db.ForeignKey('pupil.internal_id'))
    pupil = db.relationship('Pupil', back_populates='pupilgoals')

    #- RELATIONSHIP TO CATEGORY MANY-TO-ONE
    goal_category_id = db.Column('goal_category_id', db.Integer,
                                 db.ForeignKey('goal_category.id'))
    goal_category = db.relationship('GoalCategory', back_populates='categorygoals')

    #- RELATIONSHIP TO CHECKS ONE-TO-MANY
    goalchecks = db.relationship('GoalCheck', back_populates='goal',
                                 cascade="all, delete-orphan")

    def __init__(self, pupil_id, goal_category_id, goal_id, created_by, created_at, achieved,
                 achieved_at, description, strategies):
        self.pupil_id = pupil_id
        self.goal_category_id = goal_category_id
        self.goal_id = goal_id
        self.created_by = created_by
        self.created_at = created_at
        self.achieved = achieved
        self.achieved_at = achieved_at
        self.description = description
        self.strategies = strategies

class GoalCategory(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    category_id = db.Column(db.Integer, unique=True, nullable = False)
    parent_category = db.Column(db.Integer, nullable = True)
    category_name = db.Column(db.String(200), nullable = False)

    #- RELATIONSHIP TO GOALS ONE-TO-MANY
    categorygoals = db.relationship('PupilGoal', back_populates='goal_category')

    #- RELATIONSHIP TO PUPIL CATEGORY STATUS ONE-TO-MANY
    categorystatuses = db.relationship('PupilCategoryStatus',
                                       back_populates='goal_category')
    
    def __init__(self, category_id, parent_category, category_name):
        self.category_id = category_id
        self.parent_category = parent_category
        self.category_name = category_name
        

class GoalCheck(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    created_by = db.Column(db.String(20),nullable = False)
    created_at = db.Column(db.String(25), nullable = False)
    comment = db.Column(db.String(50), nullable = False)
    
    #- RELATIONSHIP TO PUPIL GOAL MANY-TO-ONE
    goal_id = db.Column(db.Integer, db.ForeignKey('pupil_goal.goal_id'))
    goal = db.relationship('PupilGoal', back_populates='goalchecks')

    def __init__(self, goal_id, created_by, created_at, comment):
        self.goal_id = goal_id
        self.created_by = created_by
        self.created_at = created_at
        self.comment = comment