# from https://www.youtube.com/watch?v=PTZiDnuC86g
# JWT from https://www.youtube.com/watch?v=WxGBoY5iNXY
from copy import error
from flask import Flask, request, jsonify, make_response
from flask_marshmallow import Marshmallow
from marshmallow import fields
from marshmallow.decorators import pre_load
from marshmallow_enum import EnumField
from datetime import datetime, timedelta
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from sqlalchemy.orm import backref
from functools import wraps

from models.pupil import *
from models.schoolday import *
from models.user import *
from models.enums import *

# Init app

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# TO-DO: implement socketio like in https://www.youtube.com/watch?v=FIBgDYA-Fas and in https://stackoverflow.com/questions/32545634/flask-a-restful-api-and-socketio-server

# Database
app.config['SECRET_KEY'] = 'THISISNOTTHEREALSECRETKEY'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init db

ma = Marshmallow(app)

#####################
#HP ADMONITION SCHEMA 
#####################

class AdmonitionSchema(ma.Schema):
    admonitiontype = EnumField(AdmonitionTypeEnum, by_value=False)
    class Meta:
        fields = ('admonishedpupil_id', 'admonishedday_id', 'admonitiontype', 'admonitionreason')

admonition_schema = AdmonitionSchema()
admonitions_schema = AdmonitionSchema(many = True)

######################
#HP MISSEDCLASS SCHEMA 
######################

class MissedClassSchema(ma.Schema):
    include_fk = True
    missedtype = EnumField(MissedTypeEnum, by_value=False)
    missed_day = ma.Function(lambda obj:obj.schoolday.schoolday.isoformat())
    # missed_schoolday = ma.Function(lambda obj:obj.schoolday.schoolday.isoformat())
    # missedpupil = ma.Function(lambda obj: obj.pupil.internal_id)
    class Meta:
        fields = ( 'missedpupil_id', 'missed_schoolday', 'missedtype', 'excused', 'contacted', 'returned', 'written_excuse', 'late_at', 'returned_at', 'created_by', 'modified_by')

missedclass_schema = MissedClassSchema()
missedclasses_schema = MissedClassSchema(many = True)

###################
#- SCHOOLDAY SCHEMA
###################

class SchooldaySchema(ma.Schema):
    missedclasses = fields.List(fields.Nested(MissedClassSchema, exclude=("missedday_id",)))
    admonitions = fields.List(fields.Nested(AdmonitionSchema, exclude=("admonishedday_id",)))
    class Meta:
        fields = ('schoolday', 'missedclasses', 'admonitions')

schoolday_schema = SchooldaySchema()
schooldays_schema = SchooldaySchema(many = True)

class PupilMissedClassSchema(ma.Schema):
    missedtype = EnumField(MissedTypeEnum, by_value=False)
    missed_day = ma.Function(lambda obj:obj.schoolday.schoolday.isoformat())
    # missed_day = missed_schoolday.strftime('%Y-%m-%d')
    class Meta:
        fields = ('missedpupil_id', 'missed_day', 'missedtype', 'excused', 'contacted', 'returned', 'written_excuse', 'late_at', 'returned_at', 'created_by', 'modified_by')


pupilmissedclass_schema = PupilMissedClassSchema()
pupilmissedclasses_schema = PupilMissedClassSchema(many = True)

class PupilAdmonitionSchema(ma.Schema):
    admonitiontype = EnumField(AdmonitionTypeEnum, by_value=False)
    admonished_day = ma.Function(lambda obj:obj.schoolday.schoolday.isoformat())
    class Meta:
        fields = ('admonishedpupil_id', 'admonished_day', 'admonitiontype', 'admonitionreason')

pupiladmonition_schema = PupilAdmonitionSchema()
pupiladmonitions_schema = PupilAdmonitionSchema(many = True)

####################
#HP WORKBOOK SCHEMA 
####################

class WorkbookSchema(ma.Schema):
    subject = EnumField(SubjectTypeEnum, by_value=False)
   # working_pupils = fields.List(fields.Nested(PupilSchema))
    class Meta:
        fields = ('isbn', 'name', 'subject')

workbook_schema = WorkbookSchema()
workbooks_schema = WorkbookSchema(many=True)

class PupilWorkbookSchema(ma.Schema):
    
    class Meta:
        fields = ('workbook_isbn', 'state', 'created_by', 'created_at' )

pupil_workbook_schema = PupilWorkbookSchema()
pupil_workbooks_schema = PupilWorkbookSchema(many=True)

################
#HP LISTS SCHEMA
################
class PupilListSchema(ma.Schema):
   
    class Meta:
        fields = ('listed_pupil_id','origin_list', 'pupil_list_status', 'pupil_list_comment', 'pupil_list_entry_by')

pupil_list_schema = PupilListSchema()
pupil_lists_schema = PupilListSchema(many=True)

class ListSchema(ma.Schema):
    pupils_in_list = fields.List(fields.Nested(PupilListSchema))
    class Meta:
        fields = ('list_id', 'list_description', 'pupils_in_list')

list_schema = ListSchema()
lists_schema = ListSchema(many= True)

############################
#HP DEVELOPMENT GOALS SCHEMA
############################

class GoalCheckSchema(ma.Schema):
    class Meta:
        fields = ('goal_id', 'created_by', 'created_at', 'comment')

goalcheck_schema = GoalCheckSchema()
goalchecks_schema = GoalCheckSchema(many = True)

class PupilGoalSchema(ma.Schema):
    goal_checks = fields.List(fields.Nested(GoalCheckSchema))
    class Meta:
        fields = ('goal_category_id', 'created_by', 'created_at', 'achieved', 'achieved_at', 'description', 'strategies', 'goal_checks')

pupilgoal_schema = PupilGoalSchema()
pupilgoals_schema = PupilGoalSchema(many = True)
# Pupil 

class GoalCategoryStatusSchema(ma.Schema):
    
    class Meta:
        fields = ('goal_category_id', 'state')    

goalcategorystatus_schema = GoalCategoryStatusSchema()
goalcategorystatuses_schema = GoalCategoryStatusSchema(many= True)

############################
#- PUPIL SCHEMA
############################

class PupilSchema(ma.Schema):
    internal_id = str(Pupil.internal_id)
    pupil_missedclasses = fields.List(fields.Nested(PupilMissedClassSchema, exclude=("missedpupil_id",)))
    pupil_admonitions = fields.List(fields.Nested(PupilAdmonitionSchema, exclude=("admonishedpupil_id",)))
    pupil_goals = fields.List(fields.Nested(PupilGoalSchema))
    pupil_category_states = fields.List(fields.Nested(GoalCategoryStatusSchema))
    pupil_workbooks = fields.List(fields.Nested(PupilWorkbookSchema))
    pupil_lists = fields.List(fields.Nested(PupilListSchema))
    
    class Meta:
        fields = ('internal_id', 'credit', 'ogs', 'individual_development_plan', 'specialneeds', 'migrationlanguagesupportends', 'migrationlanguagefollowingsupportends', 'pupil_missedclasses', 'pupil_admonitions', 'pupil_goals', 'pupil_category_states', 'pupil_workbooks', 'pupil_lists')

pupil_schema = PupilSchema()
pupils_schema = PupilSchema(many = True)

class PupilOnlyGoalSchema(ma.Schema):
    internal_id = str(Pupil.internal_id)
    pupil_goals = fields.List(fields.Nested(PupilGoalSchema))
    
    class Meta:
        fields = ('internal_id', 'pupil_goals')

pupil_only_development_goal_schema = PupilOnlyGoalSchema()
pupils_only_development_goal_schema = PupilOnlyGoalSchema(many = True)


################
#- PUPIL SCHEMA 
################

class PupilSchema(ma.Schema):
    # group = EnumField(GroupEnum, by_value=False)
    # schoolyear = EnumField(SchoolyearEnum, by_value=False)
    ## change json key like in https://stackoverflow.com/questions/51727441/marshmallow-how-can-i-map-the-schema-attribute-to-another-key-when-serializing
    internal_id = fields.String(required=True, data_key='internalId')
    individual_development_plan = fields.String(required=True, data_key='individualDevelopmentPlan')
    communication_pupil = fields.String(data_key='communicationPupil' )
    communication_tutor1 = fields.String(data_key='communicationTutor1' )
    communication_tutor2 = fields.String(data_key='communicationTutor2' )
    migration_support_ends = fields.String(data_key='migrationSupportEnds')
    migration_follow_support_ends = fields.String(data_key='migrationFollowSupportEnds')
    preschool_revision = fields.String(data_key='preschoolRevision')
    special_needs = fields.String(data_key='specialNeeds')
    pupilmissedclasses = fields.List(fields.Nested(PupilMissedClassSchema, exclude=("missedpupil_id",)))
    pupiladmonitions = fields.List(fields.Nested(PupilAdmonitionSchema, exclude=("admonishedpupil_id",)))
    pupil_workbooks = fields.List(fields.Nested(PupilWorkbookSchema))
    pupil_lists = fields.List(fields.Nested(PupilListSchema, exclude=('listed_pupil_id',)))
    class Meta:
        
        fields = ('internal_id', 'ogs', 'individual_development_plan', 'special_needs',
                  'communication_pupil', 'communication_tutor1', 'communication_tutor2',
                  'preschool_revision', 'migration_support_ends', 'migration_follow_support_ends',
                   'pupilmissedclasses', 'pupiladmonitions', 'pupil_workbooks', 'pupil_lists')

pupil_schema = PupilSchema()
pupils_schema = PupilSchema(many = True)

#################################################################################################################################
#- ##############################################################################################################################
##                   ############################################################################################################
#-     API ROUTES    ############################################################################################################
##                   ############################################################################################################
#- ##############################################################################################################################
#################################################################################################################################

#- TOKEN FUNCTION
#################

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401

        try: 
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message' : 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

###############################################################################################################
#-                      #######################################################################################
#-      API USERS       #######################################################################################
#-                      #######################################################################################
###############################################################################################################

###########
#- GET USER
###########

@app.route('/api/user', methods=['GET'])
@token_required
def get_all_users(current_user):

    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})

    users = User.query.all()

    output = []

    for user in users:
        user_data = {}
        user_data['public_id'] = user.public_id
        user_data['name'] = user.name
        user_data['password'] = user.password
        user_data['admin'] = user.admin
        output.append(user_data)

    return jsonify({'users' : output})

##############
#- POST USER
##############

@app.route('/api/user', methods=['POST'])
def create_user():
# @token_required
# def create_user(current_user):
    # if not current_user.admin:
    #     return jsonify({'message' : 'Cannot perform that function!'})

    data = request.get_json()

    is_admin = request.json['is_admin']

    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(public_id=str(uuid.uuid4()), name=data['name'], password=hashed_password, admin=is_admin)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message' : 'New user created!'})

#################
#- PUT USER
#################

@app.route('/user/<public_id>', methods=['PUT'])
@token_required
def promote_user(current_user, public_id):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message' : 'No user found!'})

    user.admin = True
    db.session.commit()

    return jsonify({'message' : 'The user has been promoted!'})

####################
#- DELETE USER
####################

@app.route('/user/<public_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, public_id):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message' : 'No user found!'})

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message' : 'The user has been deleted!'})
    
#####################
#- GET USER LOGIN 
#####################

@app.route('/api/login')
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 402, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    user = User.query.filter_by(name=auth.username).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'public_id' : user.public_id, 'exp' : datetime.utcnow() + timedelta(hours=120)},
                           app.config['SECRET_KEY'])

        return jsonify({'token' : token.decode('UTF-8')})

    return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

################################################################################################################
#-                       #######################################################################################
#-      API PUPILS       #######################################################################################
#-                       #######################################################################################
################################################################################################################

###############
#- POST PUPIL
###############

@app.route('/api/pupil', methods=['POST'])
@token_required
def add_pupil(current_user):
    internal_id = request.json['internal_id']
    credit = request.json['credit']
    ogs = request.json['ogs']
    individual_development_plan = request.json['individual_development_plan']
    special_needs = request.json['special_needs']
    communication_pupil = request.json['communication_pupil']
    communication_tutor1 = request.json['communication_tutor1']
    communication_tutor2 = request.json['communication_tutor2']
    preschool_revision = request.json['preschool_revision']
    migration_support_ends = request.json['migration_support_ends']
    migration_follow_support_ends = request.json['migration_follow_support_ends']

    new_pupil = Pupil(internal_id, credit, ogs, individual_development_plan, special_needs, communication_pupil, communication_tutor1, communication_tutor2, preschool_revision, migration_support_ends, migration_follow_support_ends)
    
    db.session.add(new_pupil)
    db.session.commit()
    return pupil_schema.jsonify(new_pupil)

# Bulk create Pupils
# https://stackoverflow.com/questions/60261701/sqlalchemy-insert-from-a-json-list-to-database

###############
#- PATCH PUPIL
###############

@app.route('/api/hermannkind/<id>', methods=['PATCH'])
@token_required
def update_pupil(current_user, id):
    pupil = Pupil.query.get(id)
    pupil.internal_id = request.json['internal_id']
    pupil.group = request.json['group']
    pupil.schoolyear = request.json['schoolyear']
    pupil.credit = request.json['credit']
    pupil.ogs = request.json['ogs']
    db.session.commit()
    return pupil_schema.jsonify(pupil)

##############################
#- PATCH PUPIL'S CREDIT
##############################

@app.route('/api/hermannkind/<id>/credit', methods=['PATCH'])
@token_required
def update_pupilcredit(current_user, id):
    pupil = Pupil.query.get(id)
    pupil.credit = request.json['credit']
    db.session.commit()
    return pupil_schema.jsonify(pupil)

###############################
#- PATCH PUPIL'S OGS STATUS
###############################

@app.route('/api/hermannkind/<id>/ogs', methods=['PATCH'])
@token_required
def update_pupilogsstatus(current_user, id):
    pupil = Pupil.query.get(id)
    pupil.ogs = request.json['ogs']
    db.session.commit()
    return pupil_schema.jsonify(pupil)

###############################
#- DELETE PUPIL
###############################

@app.route('/api/hermannkind/<id>', methods=['DELETE'])
@token_required
def delete_pupil(current_user, id):
    pupil = Pupil.query.get(id)
    db.session.delete(pupil)
    db.session.commit()
    return jsonify( {"message": "The pupil was deleted!"})

###############################
#- GET ALL PUPILS
###############################

@app.route('/api/pupils', methods=['GET'])
@token_required
def get_pupils(current_user):
    all_pupils = Pupil.query.all()
    result = pupils_schema.dump(all_pupils)
    return jsonify(result)

###############################
#- GET ALL PUPILS OF ONE CLASS
###############################

@app.route('/api/hermannkinder/<group>', methods=['GET'])
@token_required
def get_grouppupils(current_user, group):
    group_pupils = Pupil.query.filter_by(group = group).all()
    result = pupils_schema.dump(group_pupils)
    return jsonify(result)

###############################
#- GET ONE PUPIL
###############################

@app.route('/api/hermannkind/<id>', methods=['GET'])
@token_required
def get_pupil(current_user, id):
    this_pupil = db.session.query(Pupil).get(id)
    return pupil_schema.jsonify(this_pupil)

###################################################################################################################
#-                          #######################################################################################
#-      API WORKBOOKS       #######################################################################################
#-                          #######################################################################################
###################################################################################################################

###############################
#- GET WORKBOOKS CATALOGUE
###############################

@app.route('/api/workbook/all', methods=['GET'])
@token_required
def get_workbooks(current_user):
    all_workbooks = Workbook.query.all()
    result = workbooks_schema.dump(all_workbooks)
    return jsonify(result)

###############################
#- POST WORKBOOK
###############################

@app.route('/api/workbook/new', methods=['POST'])
@token_required
def create_workbook(current_user):
    isbn = request.json['isbn']
    name = request.json['name']
    subject = request.json['subject']

    if subject not in subject_enums:
        return jsonify({"message": "Das Fach ist nicht zulässig!"})

    new_workbook = Workbook(isbn, name, subject)
    db.session.add(new_workbook)
    db.session.commit()
    return workbook_schema.jsonify(new_workbook)

###############################
#- DELETE WORKBOOK
###############################

@app.route('/api/workbook/<isbn>', methods=['DELETE'])
@token_required
def delete_workbook(current_user, isbn):
    this_workbook = Workbook.query.filter_by(isbn = isbn).first()

    db.session.delete(this_workbook)
    db.session.commit()
    return jsonify( {"message": "Arbeitsheft aus dem Katalog gelöscht!"})

###############################
#- POST PUPIL WORKBOOK
###############################

@app.route('/api/kind/<internal_id>/workbook/<isbn>', methods=['POST'])
@token_required
def add_workbook_to_pupil(current_user, internal_id, isbn):
    this_pupil = Pupil.query.filter_by(internal_id = internal_id).first()
    pupil_id = internal_id
    isbn = isbn
    state = 'active'
    created_by = current_user.name
    created_at = datetime.now()

    new_pupil_workbook = PupilWorkbook(pupil_id, isbn, state, created_by, created_at)
    db.session.add(new_pupil_workbook)
    db.session.commit()
    return pupil_schema.jsonify(this_pupil)

###############################
#- PATCH PUPIL WORKBOOK STATE
###############################

@app.route('/api/kind/<internal_id>/workbook/<isbn>', methods=['PATCH'])
@token_required
def update_PupilWorkbook(current_user, internal_id, isbn):
    this_pupil = Pupil.query.filter_by(internal_id = internal_id).first()
    this_workbook = PupilWorkbook.query.filter_by(pupil_id = internal_id, workbook_isbn = isbn).first()
    this_workbook.state = request.json['state']
    db.session.commit()
    return pupil_schema.jsonify(this_pupil)

###############################
#- DELETE PUPIL WORKBOOK
###############################

@app.route('/api/kind/<internal_id>/workbook/<isbn>', methods=['DELETE'])
@token_required
def delete_PupilWorkbook(current_user, internal_id, isbn):
    this_workbook = PupilWorkbook.query.filter_by(pupil_id = internal_id, workbook_isbn = isbn).first()
    db.session.delete(this_workbook)
    db.session.commit()
    return jsonify( {"message": "Das Arbeitsheft wurde gelöscht!"})

###################################################################################################################
#-                          #######################################################################################
#-        API GOALS         #######################################################################################
#-                          #######################################################################################
###################################################################################################################


###############################
#- GET CATEGORIES
###############################

@app.route('/api/goalcategories', methods=['GET'])
@token_required
def get_categories(current_user):
    root = {
        "category_id": 0,
        "category_name": "development_goal_categories",
        "subcategories": [],
    }
    dict = {0: root}
    all_categories = GoalCategory.query.all()
    for item in all_categories:
        dict[item.category_id] = current = {
            "category_id": item.category_id,
            "parent_category": item.parent_category,
            "category_name": item.category_name,
            "subcategories": [],
        }
        # Adds actual category to the subcategories list of the parent
        parent = dict.get(item.parent_category, root)
        parent["subcategories"].append(current)

    return jsonify(root)

###############################
#- POST GOAL
###############################

@app.route('/api/kind/<internal_id>/goal', methods=['POST'])
@token_required
def add_goal(current_user, internal_id):
    pupil = Pupil.query.filter_by(internal_id = internal_id).first()
    pupilid = pupil.internal_id
    goalcategoryid = request.json['goal_category_id']
    created_by = current_user.name
    created_at = request.json['created_at']
    achieved = request.json['achieved']
    achieved_at = request.json['achieved_at']
    description = request.json['description']
    strategies = request.json['strategies']

    new_goal = PupilGoal(pupilid, goalcategoryid, created_by, created_at, achieved, achieved_at, description, strategies)
    db.session.add(new_goal)
    db.session.commit()
    return pupilgoal_schema.jsonify(new_goal)

###############################
#- PUT GOAL
###############################

@app.route('/api/kind/<internal_id>/goal/<goal_id>', methods=['PUT'])
@token_required
def put_goal(current_user, internal_id, goal_id):
    goal = PupilGoal.query.filter_by(id = goal_id).first()
    goal.pupil_id = internal_id
    goal.goalcategoryid = request.json['goal_category_id']
    goal.created_by = current_user.name
    goal.created_at = request.json['created_at']
    goal.achieved = request.json['achieved']
    goal.achieved_at = request.json['achieved_at']
    goal.description = request.json['description']
    goal.strategies = request.json['strategies']

    db.session.commit()
    return pupilgoal_schema.jsonify(goal)

###############################
#- POST GOAL CHECK
###############################

@app.route('/api/kind/goal/<goal_id>/check', methods=['POST'])
@token_required
def add_goalcheck(current_user, goal_id):
    this_goal = PupilGoal.query.filter_by(id = goal_id).first()
    this_goal_id = goal_id
    created_by = current_user.name
    created_at = request.json['created_at']
    comment = request.json['comment']

    new_goalcheck = GoalCheck(this_goal_id, created_by, created_at, comment)
    db.session.add(new_goalcheck)
    db.session.commit()
    return pupilgoal_schema.jsonify(this_goal)

###############################
#- PUT GOAL CHECK
###############################

@app.route('/api/kind/goal/check/<id>', methods=['PUT'])
@token_required
def put_goalcheck(current_user, id):
    goal = GoalCheck.query.filter_by(id = id).first()
    goal.created_by = current_user.name
    goal.created_at = request.json['created_at']
    goal.comment = request.json['comment']
    db.session.commit()
    return pupilgoal_schema.jsonify(goal)

###############################
#- POST GATEGORY STATE
###############################

@app.route('/api/kind/<internal_id>/categorystatus/<category_id>', methods=['POST'])
@token_required
def add_category_state(current_user, internal_id, category_id):
    this_pupil = Pupil.query.filter_by(internal_id = internal_id).first()
    pupil_id = internal_id
    goal_category_id = category_id
    state = request.json['state']
    created_by = current_user.name
    created_at = request.json['created_at']

    new_category_status = PupilCategoryStatus(pupil_id, goal_category_id, state, created_by, created_at)
    db.session.add(new_category_status)
    db.session.commit()
    return pupil_schema.jsonify(this_pupil)

###############################
#- PUT GATEGORY STATE
###############################

@app.route('/api/kind/<internal_id>/categorystatus/<status_id>', methods=['PUT'])
@token_required
def put_category_state(current_user, internal_id, status_id):
    this_pupil = Pupil.query.filter_by(internal_id = internal_id).first()
    status = PupilCategoryStatus.query.filter_by(id = status_id).first()
    status.pupil_id = internal_id
    status.goal_category_id = request.json['goal_category_id']
    status.state = request.json['state']
    status.created_by = current_user.name
    status.created_at = request.json['created_at']

    db.session.commit()
    return pupil_schema.jsonify(this_pupil)

###################################################################################################################
#-                          #######################################################################################
#-        API LISTS         #######################################################################################
#-                          #######################################################################################
###################################################################################################################

###############################
#- POST LIST
###############################

@app.route('/api/list/new', methods=['POST'])
@token_required
def add_list(current_user):
    
    list_id = str(uuid.uuid4())
    list_description = request.json['list_description']
    new_list = List(list_id, list_description)
    db.session.add(new_list)
    all_pupils = Pupil.query.all()
    
    for item in all_pupils:
        origin_list = list_id
        listed_pupil_id = item.internal_id
        pupil_list_status = False
        pupil_list_comment = ''
        pupil_list_entry_by = ''
        new_pupil_list = PupilList(origin_list, listed_pupil_id, pupil_list_status, pupil_list_comment, pupil_list_entry_by)
        db.session.add(new_pupil_list)
        db.session.commit()
    return list_schema.jsonify(new_list)

###############################
#- GET LISTS
###############################

@app.route('/api/list/all', methods=['GET'])
@token_required
def get_lists(current_user):
    all_lists = List.query.all()
    result = lists_schema.dump(all_lists)
    return jsonify(result)

####################################################################################################################
#-                           #######################################################################################
#-      API SCHOOLDAYS       #######################################################################################
#-                           #######################################################################################
####################################################################################################################

###############################
#- POST SCHOOLDAY
###############################

@app.route('/api/schoolday', methods=['POST'])
@token_required
def add_schoolday(current_user):
    schoolday = request.json['schoolday']
    stringtodatetime = datetime.strptime(schoolday, '%Y-%m-%d').date()
    exists = db.session.query(Schoolday).filter_by(schoolday= stringtodatetime).scalar() is not None 
    if exists == True:
        return jsonify( {"message": "This schoolday exists already!"})
    else:    
        new_schoolday = Schoolday(stringtodatetime) 
        db.session.add(new_schoolday)
        db.session.commit()
        return schoolday_schema.jsonify(new_schoolday)

###############################
#- GET ALL SCHOOLDAYS
###############################

@app.route('/api/schultage', methods=['GET'])
@token_required
def get_schooldays(current_user):
    all_schooldays = db.session.query(Schoolday).all()
    result = schooldays_schema.dump(all_schooldays)
    return jsonify(result)

###############################
#- GET ONE SCHOOLDAY
###############################

@app.route('/api/schultag/<date>', methods=['GET'])
@token_required
def get_schooday(current_user, date):
    stringtodatetime = datetime.strptime(date, '%Y-%m-%d').date()
    this_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    return schoolday_schema.jsonify(this_schoolday)

###############################
#- DELETE ONE SCHOOLDAY
###############################

@app.route('/api/schultag/<date>', methods=['DELETE'])
@token_required
def delete_schoolday(current_user, date):
    stringtodatetime = datetime.strptime(date, '%Y-%m-%d').date()
    this_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    db.session.delete(this_schoolday)
    db.session.commit()
    return jsonify( {"message": "The schoolday was deleted!"})

######################################################################################################################
#-                             #######################################################################################
#-      API MISSED CLASS       #######################################################################################
#-                             #######################################################################################
######################################################################################################################

###############################
#- POST MISSED CLASS
###############################

@app.route('/api/missed_class', methods=['POST'])
@token_required
def add_missedclass(current_user):
    missedpupil_id = request.json['missedpupil_id']
    missedday = request.json['missed_day']
    stringtodatetime = datetime.strptime(missedday, '%Y-%m-%d').date()
    this_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    missedday_id = this_schoolday.id
    missedclass_exists = db.session.query(MissedClass).filter(MissedClass.missedday_id == missedday_id, MissedClass.missedpupil_id == missedpupil_id ).first() is not None
    if missedclass_exists == True :
        return jsonify( {"message": "This missed class exists already - please update instead!"})
    else:    
        missedtype = request.json['missed_type']
        excused = request.json['excused']
        contacted = request.json['contacted']
        returned = request.json['returned']
        returned_at = request.json['returnedAt']
        late_at = request.json['lateAt']
        written_excuse = request.json['writtenExcuse']
        created_by = current_user.name
        modified_by = None
        new_missedclass = MissedClass(missedpupil_id, missedday_id, missedtype, excused, contacted, returned, written_excuse, late_at, returned_at, created_by, modified_by)

        db.session.add(new_missedclass)
        db.session.commit()
        return missedclass_schema.jsonify(new_missedclass)

###############################
#- GET ALL MISSED CLASSES
###############################

@app.route('/api/fehlzeiten', methods=['GET'])
@token_required
def get_missedclasses(current_user):
    all_missedclasses = MissedClass.query.all()
    result = pupilmissedclasses_schema.dump(all_missedclasses)
    return jsonify(result)

###############################
#- GET ONE MISSED CLASS
###############################

@app.route('/api/fehlzeit/<id>', methods=['GET'])
@token_required
def get_missedclass(current_user, id):
    this_missedclass = db.session.query(MissedClass).get(id)
    return pupilmissedclass_schema.jsonify(this_missedclass)

###############################
#- PATCH MISSED CLASS
###############################

@app.route('/api/fehlzeit/<id>/<date>', methods=['PATCH'])
@token_required
def update_missedclass(current_user, id, date):
    stringtodatetime = datetime.strptime(date, '%Y-%m-%d').date()
    missed_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    missedday_id = missed_schoolday.id
    missedpupil_id = id
    missedclass = db.session.query(MissedClass).filter(MissedClass.missedday_id == missedday_id, MissedClass.missedpupil_id == missedpupil_id ).first()
    missedclass.missedtype = request.json['missedtype']
    missedclass.excused = request.json['excused']
    missedclass.contacted = request.json['contacted']
    db.session.commit()
    return missedclass_schema.jsonify(missedclass)

###############################
#- PATCH MISSED CLASS (MISSED TYPE)
###############################

@app.route('/api/fehlzeit/type/<id>/<date>', methods=['PATCH'])
@token_required
def update_missedclass_type_with_date(current_user, id, date):
    
    stringtodatetime = datetime.strptime(date, '%Y-%m-%d').date()
    missed_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    missedday_id = missed_schoolday.id
    missedpupil_id = id
    missedclass = db.session.query(MissedClass).filter(MissedClass.missedday_id == missedday_id, MissedClass.missedpupil_id == missedpupil_id ).first()
    missedclass.missedtype = request.json['missedtype']
    
    db.session.commit()
    return missedclass_schema.jsonify(missedclass)

###############################
#- PATCH MISSED CLASS (EXCUSED BOOL)
###############################

@app.route('/api/fehlzeit/status/<id>/<date>', methods=['PATCH'])
@token_required
def update_missedclass_excused_status_with_date(current_user, id, date):
    
    stringtodatetime = datetime.strptime(date, '%Y-%m-%d').date()
    missed_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    missedday_id = missed_schoolday.id
    missedpupil_id = id
    missedclass = db.session.query(MissedClass).filter(MissedClass.missedday_id == missedday_id, MissedClass.missedpupil_id == missedpupil_id ).first()
    missedclass.excused = request.json['excused']
    
    db.session.commit()
    return missedclass_schema.jsonify(missedclass)

###############################
#- PATCH MISSED CLASS (CONTACTED BOOL)
###############################

@app.route('/api/fehlzeit/contacted/<id>/<date>', methods=['PATCH'])
@token_required
def update_missedclass_contacted_status_with_date(current_user, id, date):
    
    stringtodatetime = datetime.strptime(date, '%Y-%m-%d').date()
    missed_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    missedday_id = missed_schoolday.id
    missedpupil_id = id
    missedclass = db.session.query(MissedClass).filter(MissedClass.missedday_id == missedday_id, MissedClass.missedpupil_id == missedpupil_id ).first()
    missedclass.contacted = request.json['contacted']
    
    db.session.commit()
    return missedclass_schema.jsonify(missedclass)

###############################
#- DELETE MISSED CLASS WITH DATE
###############################

@app.route('/api/fehlzeit/<pupil_id>/<date>', methods=['DELETE'])
@token_required
def delete_missedclass_with_date(current_user, pupil_id, date):
    
    stringtodatetime = datetime.strptime(date, '%Y-%m-%d').date()
    missed_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    thismissedday_id = missed_schoolday.id
    missed_schoolday = db.session.query(MissedClass).filter(Schoolday.schoolday == stringtodatetime ).first()
    missedpupil_id = pupil_id
    missedclass = db.session.query(MissedClass).filter(MissedClass.missedday_id == thismissedday_id, MissedClass.missedpupil_id == missedpupil_id ).first() 
  
    db.session.delete(missedclass)
    db.session.commit()
    return jsonify( {"message": "The missed class was deleted!"})
   
###############################
#- DELETE MISSED CLASS WITH ID
###############################

@app.route('/api/fehlzeit/<id>', methods=['DELETE'])
@token_required
def delete_missedclass(current_user, id):
    missedclass = db.session.query(MissedClass).get(id)
    db.session.delete(missedclass)
    db.session.commit()
    return jsonify( {"message": "The missed class was deleted!"})

#####################################################################################################################
#-                            #######################################################################################
#-      API ADMONITIONS       #######################################################################################
#-                            #######################################################################################
#####################################################################################################################

###############################
#- POST ADMONITION
###############################

@app.route('/api/karte', methods=['POST'])
@token_required
def add_admonition(current_user):
    admonishedpupil_id = request.json['admonishedpupil_id']
    admonishedday = request.json['admonishedday']
    stringtodatetime = datetime.strptime(admonishedday, '%Y-%m-%d').date()
    this_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    admonishedday_id = this_schoolday.id
    day_exists = db.session.query(Admonition).filter_by(admonishedday_id = this_schoolday.id).scalar() is not None
    pupil_exists = db.session.query(Admonition).filter_by(admonishedpupil_id = admonishedpupil_id).scalar is not None
    if day_exists == True and pupil_exists == True:
        return jsonify( {"message": "This missed class exists already - please update instead!"})
    else:    
        admonitiontype = request.json['admonitiontype']
        admonitionreason = request.json['admonitionreason']
        new_admonition = Admonition(admonishedpupil_id, admonishedday_id, admonitiontype, admonitionreason)
        db.session.add(new_admonition)
        db.session.commit()
        return admonition_schema.jsonify(new_admonition)

###############################
#- GET ADMONITIONS
###############################

@app.route('/api/karten', methods=['GET'])
@token_required
def get_admonitions(current_user):
    all_admonitions = Admonition.query.all()
    result = pupiladmonitions_schema.dump(all_admonitions)
    return jsonify(result)

###############################
#- GET ONE ADMONITION
###############################

@app.route('/api/karte/<id>', methods=['GET'])
@token_required
def get_admonition(current_user, id):
    this_admonition = db.session.query(Admonition).get(id)
    return pupiladmonition_schema.jsonify(this_admonition)

###############################
#- PATCH ADMONITION
###############################

@app.route('/api/karte/<id>', methods=['PATCH'])
@token_required
def update_admonition(current_user, id):
    admonition = Admonition.query.get(id)
    admonition.admonitiontype = request.json['admonitiontype']
    admonition.admonitionreason = request.json['admonitionreason']
    db.session.commit()
    return admonition_schema.jsonify(admonition)

###############################
#- DELETE ADMONITION BY ID
###############################

@app.route('/api/karte/<id>', methods=['DELETE'])
@token_required
def delete_admonition(current_user, id):
    admonition = db.session.query(Admonition).get(id)
    db.session.delete(admonition)
    db.session.commit()
    return jsonify( {"message": "The admonition was deleted!"})

##########################################
#- DELETE ADMONITION BY PUPIL_ID AND DATE
##########################################

@app.route('/api/karte/<pupil_id>/<date>', methods=['DELETE'])
@token_required
def delete_admonition_by_day(current_user, pupil_id, date):
    stringtodatetime = datetime.strptime(date, '%Y-%m-%d').date()
    admonished_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    thisadmonishedday_id = admonished_schoolday.id
    missedpupil_id = pupil_id
    admonition = db.session.query(Admonition).filter(Admonition.admonishedday_id == thisadmonishedday_id, Admonition.admonishedpupil_id == missedpupil_id ).first() 
    db.session.delete(admonition)
    db.session.commit()
    return jsonify( {"message": "The admonition was deleted!"})

# Run server
# db.init_app(app) because of https://stackoverflow.com/questions/9692962/flask-sqlalchemy-import-context-issue/9695045#9695045
db.init_app(app)
with app.app_context():
    db.drop_all()
    db.create_all()
if __name__ == '__main__':
    app.run(debug=True)
