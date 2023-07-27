from copy import error
from flask import Flask, request, jsonify, make_response, send_file
from flask_marshmallow import Marshmallow
from marshmallow import fields
from marshmallow.decorators import pre_load
from marshmallow_enum import EnumField
from datetime import datetime, timedelta
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps

from pprint import pprint

from io import TextIOWrapper
import csv

from models.pupil import *
from models.schoolday import *
from models.user import *
from models.enums import *

#- Init app

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

#- APP CONFIG

app.config['SECRET_KEY'] = 'THISISNOTTHEREALSECRETKEY'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = './media_upload'
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg'])
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower in ALLOWED_EXTENSIONS


#- MARSHMALLOW SCHEMAS

ma = Marshmallow(app)

# #####################
# #- ADMONITION SCHEMA 
# #####################

class AdmonitionSchema(ma.Schema):
    admonition_type = EnumField(AdmonitionTypeEnum, by_value=False)
    class Meta:
        fields = ('admonishedpupil_id', 'admonished_day_id', 'admonition_type',
                  'admonition_reason')

admonition_schema = AdmonitionSchema()
admonitions_schema = AdmonitionSchema(many = True)

######################
#- MISSEDCLASS SCHEMA - CHECKED
######################

class MissedClassSchema(ma.Schema):
    include_fk = True
    missed_type = EnumField(MissedTypeEnum, by_value=False)
    missed_day = ma.Pluck('SchooldaySchema', 'schoolday')
    class Meta:
        fields = ( 'missed_pupil_id', 'missed_day', 'missed_type',
                  'excused', 'contacted', 'returned', 'written_excuse', 'late_at',
                  'returned_at', 'created_by', 'modified_by')

missedclass_schema = MissedClassSchema()
missedclasses_schema = MissedClassSchema(many = True)

###################
#- SCHOOLDAY SCHEMA - CHECKED
###################

class SchooldaySchema(ma.Schema):
    missedclasses = fields.List(fields.Nested(MissedClassSchema, exclude=("missed_day",)))
    admonitions = fields.List(fields.Nested(AdmonitionSchema))
    class Meta:
        fields = ('schoolday', 'missedclasses', 'admonitions')

schoolday_schema = SchooldaySchema()
schooldays_schema = SchooldaySchema(many = True)

# #####################
#- PUPIL ADMONITION SCHEMA 
# #####################

class PupilAdmonitionSchema(ma.Schema):
    include_fk = True
    admonition_type = EnumField(AdmonitionTypeEnum, by_value=False)
    admonished_day = ma.Pluck(SchooldaySchema, 'schoolday')
    class Meta:
        fields = ('admonishedpupil_id', 'admonished_day', 'admonition_type', 'admonition_reason')

pupiladmonition_schema = PupilAdmonitionSchema()
pupiladmonitions_schema = PupilAdmonitionSchema(many = True)

####################
#- WORKBOOK SCHEMA - CHECKED
####################

class PupilWorkbookSchema(ma.Schema):
    class Meta:
        fields = ('workbook_isbn', 'state', 'created_by', 'created_at' )

pupil_workbook_schema = PupilWorkbookSchema()
pupilworkbooks_schema = PupilWorkbookSchema(many=True)

class PupilWorkbookListSchema(ma.Schema):
    
    class Meta:
        fields = ('pupil_id', 'state', 'created_by', 'created_at' )

pupil_workbook_list_schema = PupilWorkbookListSchema()
pupilworkbooks_list_schema = PupilWorkbookListSchema(many=True)

class WorkbookSchema(ma.Schema):
    subject = EnumField(SubjectTypeEnum, by_value=False)
    workbookpupils = fields.List(fields.Nested(PupilWorkbookListSchema))
    class Meta:
        fields = ('isbn', 'name', 'subject', 'workbookpupils')

workbook_schema = WorkbookSchema()
workbooks_schema = WorkbookSchema(many=True)

################
#- LISTS SCHEMA - CHECKED
################

class PupilListSchema(ma.Schema):
    class Meta:
        fields = ('listed_pupil_id','pupil_list_status', 'pupil_list_comment',
                  'pupil_list_entry_by')

pupil_list_schema = PupilListSchema()
pupil_lists_schema = PupilListSchema(many=True)

class PupilProfileListSchema(ma.Schema): 
    class Meta:
        fields = ('origin_list', 'pupil_list_status', 'pupil_list_comment',
                  'pupil_list_entry_by')

pupilprofilelist_schema = PupilListSchema()
pupilprofilelists_schema = PupilListSchema(many=True)

class SchoolListSchema(ma.Schema):
    pupilsinlist = fields.List(fields.Nested(PupilListSchema))
    
    class Meta:
        fields = ('list_id', 'list_name', 'list_description', 'created_by', 'pupilsinlist')

school_list_schema = SchoolListSchema()
school_lists_schema = SchoolListSchema(many= True)

############################
#- DEVELOPMENT GOALS SCHEMA - CHECKED
############################

class GoalCheckSchema(ma.Schema):
    class Meta:
        fields = ('created_by', 'created_at', 'comment')

goalcheck_schema = GoalCheckSchema()
goalchecks_schema = GoalCheckSchema(many = True)

class PupilGoalSchema(ma.Schema):
    goalchecks = fields.List(fields.Nested(GoalCheckSchema))
    class Meta:
        fields = ('goal_id', 'goal_category_id', 'created_by', 'created_at', 'achieved',
                  'achieved_at', 'description', 'strategies', 'goalchecks')

pupilgoal_schema = PupilGoalSchema()
pupilgoals_schema = PupilGoalSchema(many = True)
pupilgoals_schema = PupilGoalSchema(many = True)
# Pupil 
pupilgoals_schema = PupilGoalSchema(many = True) 
# Pupil 

class PupilCategoryStatusSchema(ma.Schema):
    
    class Meta:
        fields = ('goal_category_id', 'state')    

pupilcategorystatus_schema = PupilCategoryStatusSchema()
pupilcategorystatuses_schema = PupilCategoryStatusSchema(many= True)

class GoalCategorySchema(ma.Schema):
    categorygoals = fields.List(fields.Nested(PupilGoalSchema))
    categorystatuses = fields.List(fields.Nested(PupilCategoryStatusSchema))

    class Meta:
        fields = ('category_id', 'category_name', 'categorygoals',
                  'categorystatuses')

goalcategory_schema = GoalCategorySchema()
goalcategories_schema = GoalCategorySchema(many = True)

############################
#- PUPIL SCHEMA - CHECKED
############################

class PupilSchema(ma.Schema):
    internal_id = str(Pupil.internal_id)
    pupilmissedclasses = fields.List(fields.Nested(MissedClassSchema,
                                                   exclude=("missed_pupil_id",)))
    pupiladmonitions = fields.List(fields.Nested(PupilAdmonitionSchema))
    pupilgoals = fields.List(fields.Nested(PupilGoalSchema))
    pupilcategorystatuses = fields.List(fields.Nested(PupilCategoryStatusSchema))
    pupilworkbooks = fields.List(fields.Nested(PupilWorkbookSchema))
    pupillists = fields.List(fields.Nested(PupilProfileListSchema))
    
    class Meta:
        fields = ('internal_id', 'credit', 'ogs', 
                  'individual_development_plan', 'five_years', 
                  'special_needs', 'communication_pupil', 
                  'communication_tutor1', 'communication_tutor2', 
                  'preschool_revision', 'migration_support_ends', 
                  'migration_follow_support_ends', 'pupilmissedclasses', 
                  'pupiladmonitions', 'pupilgoals', 'pupilcategorystatuses', 
                  'pupilworkbooks', 'pupillists', 'avatar_url', 'special_information')

pupil_schema = PupilSchema()
pupils_schema = PupilSchema(many = True)

class PupilOnlyGoalSchema(ma.Schema):
    internal_id = str(Pupil.internal_id)
    pupilgoals = fields.List(fields.Nested(PupilGoalSchema))
    
    class Meta:
        fields = ('internal_id', 'pupilgoals')

pupil_only_goal_schema = PupilOnlyGoalSchema()
pupils_only_goal_schema = PupilOnlyGoalSchema(many = True)

########################################
#- #####################################
##                   ###################
#-     API ROUTES    ###################
##                   ###################
#- #####################################
########################################

#- TOKEN FUNCTION
#################
# JWT from https://www.youtube.com/watch?v=WxGBoY5iNXY

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
            current_user = User.query.filter_by(public_id=
                                                data['public_id']).first()
        except:
            return jsonify({'message' : 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

##########################################
#-                      ##################
#-      API USERS       ##################
#-                      ##################
##########################################

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
#- POST USER * TESTED
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

    new_user = User(public_id=str(uuid.uuid4().hex), name=data['name'],
                     password=hashed_password, admin=is_admin)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message' : 'New user created!'})

#################
#- PUT USER *T ESTED
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
        return make_response('Could not verify', 402,
                             {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    user = User.query.filter_by(name=auth.username).first()

    if not user:
        return make_response('Could not verify', 401,
                             {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'public_id' : user.public_id, 'exp' :
                            datetime.utcnow() + timedelta(hours=120)},
                           app.config['SECRET_KEY'])

        return jsonify({'token' : token.decode('UTF-8')})

    return make_response('Could not verify', 401,
                         {'WWW-Authenticate' : 'Basic realm="Login required!"'})

###############################################
#-                       ######################
#-      API PUPILS       ######################
#-                       ######################
###############################################

###############
#- POST PUPIL * TESTED
###############

@app.route('/api/pupil', methods=['POST'])
@token_required
def add_pupil(current_user):
    internal_id = request.json['internal_id']
    exists = db.session.query(Pupil).filter_by(internal_id= internal_id).scalar() is not None 
    if exists == True:
        return jsonify( {"message": "This pupil exists already - please update the page!"})
    else:     
        credit = request.json['credit']
        ogs = request.json['ogs']
        five_years = request.json['five_years']
        individual_development_plan = request.json['individual_development_plan']
        special_needs = request.json['special_needs']
        communication_pupil = request.json['communication_pupil']
        communication_tutor1 = request.json['communication_tutor1']
        communication_tutor2 = request.json['communication_tutor2']
        preschool_revision = request.json['preschool_revision']
        avatar_url = request.json['avatar_url']
        special_information = request.json['special_information']
        if request.json['migration_support_ends'] != None:
            migration_support_ends = datetime.strptime(request.json['migration_support_ends'], '%Y-%m-%d').date() 
        else:
            migration_support_ends = request.json['migration_support_ends']
        if request.json['migration_follow_support_ends'] != None:
            migration_follow_support_ends = datetime.strptime(request.json['migration_follow_support_ends'], '%Y-%m-%d').date()
        else:
            migration_follow_support_ends = request.json['migration_follow_support_ends']
        new_pupil = Pupil(internal_id, credit, ogs, individual_development_plan, five_years,
                        special_needs, communication_pupil, communication_tutor1,
                        communication_tutor2, preschool_revision, migration_support_ends,
                        migration_follow_support_ends, avatar_url, special_information)       
        db.session.add(new_pupil)
        db.session.commit()
        return pupil_schema.jsonify(new_pupil)

###############
#- PATCH PUPIL * TESTED
###############

@app.route('/api/pupil/<internal_id>', methods=['PATCH'])
@token_required
def update_pupil(current_user, internal_id):
    pupil = Pupil.query.filter_by(internal_id = internal_id).first()
    data = request.get_json()
    for key in data:
        match key:
            case 'credit':
                pupil.credit = data[key] 
            case 'ogs':
                pupil.ogs = data[key] 
            case 'five_years':
                pupil.five_years = data[key] 
            case'special_needs':            
                pupil.special_needs = data[key] 
            case'special_needs':            
                pupil.special_needs = data[key]           
            case'communication_pupil':            
                pupil.communication_pupil = data[key] 
            case'communication_tutor1':            
                pupil.communication_tutor1 = data[key] 
            case'communication_tutor2':            
                pupil.communication_tutor2 = data[key] 
            case'preschool_revision':            
                pupil.preschool_revision = data[key] 
            case'migration_support_ends':
                if data[key] != None:            
                    pupil.migration_support_ends = datetime.strptime(data[key], '%Y-%m-%d').date()
                else:
                    pupil.migration_support_ends = None
            case'migration_follow_support_ends':            
                if data[key] != None:
                    pupil.migration_follow_support_ends = datetime.strptime(data[key], '%Y-%m-%d').date()
                else:
                    pupil.migration_follow_support_ends = None
            case'special_information':            
                pupil.special_information = data[key]                 
    db.session.commit()
    return pupil_schema.jsonify(pupil)

###############################
#- GET ALL PUPILS * TESTED
###############################

@app.route('/api/pupil/all', methods=['GET'])
@token_required
def get_pupils(current_user):
    all_pupils = Pupil.query.all()
    result = pupils_schema.dump(all_pupils)
    return jsonify(result)

###############################
#- GET LISTED PUPILS * TESTED
###############################

@app.route('/api/pupil/list', methods=['GET'])
@token_required
def get_given_pupils(current_user):
    internal_id_list = request.json['pupils']
    pupils_list = []
    for item in internal_id_list:
        this_pupil = db.session.query(Pupil).filter(Pupil.internal_id ==
                                                    item).first()
        pupils_list.append(this_pupil)
    result = pupils_schema.dump(pupils_list)
    return jsonify(result)

###############################
#- GET ONE PUPIL * TESTED
###############################

@app.route('/api/pupil/<internal_id>', methods=['GET'])
@token_required
def get_pupil(current_user, internal_id):
    this_pupil = db.session.query(Pupil).filter(Pupil.internal_id == 
                                                internal_id).first()
    return pupil_schema.jsonify(this_pupil)

###############################
#- DELETE PUPIL * TESTED
###############################

@app.route('/api/pupil/<internal_id>', methods=['DELETE'])
@token_required
def delete_pupil(current_user, internal_id):
    pupil = Pupil.query.filter_by(internal_id = internal_id).first()
    if len(str(pupil.avatar_url)) > 4:
        os.remove(str(pupil.avatar_url))
    db.session.delete(pupil)
    db.session.commit()
    return jsonify( {"message": "The pupil was deleted!"})

###################################################
#-                          #######################
#-      API WORKBOOKS       #######################
#-                          #######################
###################################################

###############################
#- GET WORKBOOKS * TESTED
###############################

@app.route('/api/workbook/all', methods=['GET'])
@token_required
def get_workbooks(current_user):
    all_workbooks = Workbook.query.all()
    result = workbooks_schema.dump(all_workbooks)
    return jsonify(result)

###############################
#- POST WORKBOOK * TESTED
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
#- DELETE WORKBOOK * TESTED
###############################

@app.route('/api/workbook/<isbn>', methods=['DELETE'])
@token_required
def delete_workbook(current_user, isbn):
    this_workbook = Workbook.query.filter_by(isbn = isbn).first()
    db.session.delete(this_workbook)
    db.session.commit()
    return jsonify( {"message": "Arbeitsheft aus dem Katalog gelöscht!"})

###############################
#- POST PUPIL WORKBOOK * TESTED
###############################

@app.route('/api/pupil/<internal_id>/workbook/<isbn>', methods=['POST'])
@token_required
def add_workbook_to_pupil(current_user, internal_id, isbn):
    this_pupil = Pupil.query.filter_by(internal_id = internal_id).first()
    pupil_id = internal_id
    isbn = isbn
    state = 'active'
    created_by = current_user.name
    created_at = datetime.now().date()
    new_pupil_workbook = PupilWorkbook(pupil_id, isbn, state, created_by, created_at)
    db.session.add(new_pupil_workbook)
    db.session.commit()
    return pupil_workbook_schema.jsonify(new_pupil_workbook)

###############################
#- PATCH PUPIL WORKBOOK  * TESTED
###############################

@app.route('/api/pupil/<internal_id>/workbook/<isbn>', methods=['PATCH'])
@token_required
def update_PupilWorkbook(current_user, internal_id, isbn):
    pupil_workbook = PupilWorkbook.query.filter_by(pupil_id = internal_id,
                                                  workbook_isbn = isbn).first()
    data = request.get_json()
    for key in data:
        match key:
            case 'state':
                pupil_workbook.state = data[key]
            case 'created_by':
                pupil_workbook.created_by = data[key]
            case 'created_at':
                pupil_workbook.created_at = data[key]
    db.session.commit()
    return pupil_workbook_list_schema.jsonify(pupil_workbook)

###############################
#- DELETE PUPIL WORKBOOK
###############################

@app.route('/api/pupil/<internal_id>/workbook/<isbn>', methods=['DELETE'])
@token_required
def delete_PupilWorkbook(current_user, internal_id, isbn):
    this_workbook = PupilWorkbook.query.filter_by(pupil_id = internal_id,
                                                  workbook_isbn = isbn).first()
    db.session.delete(this_workbook)
    db.session.commit()
    return jsonify( {"message": "Das Arbeitsheft wurde gelöscht!"})

###############################################
#-                          ###################
#-        API GOALS         ###################
#-                          ###################
###############################################

###############################
#- GET CATEGORIES * TESTED
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
#- POST GOAL * TESTED
###############################

@app.route('/api/pupil/<internal_id>/goal', methods=['POST'])
@token_required
def add_goal(current_user, internal_id):
    pupil = Pupil.query.filter_by(internal_id = internal_id).first()
    pupil_id = pupil.internal_id
    goal_category_id = request.json['goal_category_id']
    goal_id = str(uuid.uuid4().hex)
    created_by = current_user.name
    created_at = request.json['created_at']
    achieved = request.json['achieved']
    achieved_at = request.json['achieved_at']
    description = request.json['description']
    strategies = request.json['strategies']
    new_goal = PupilGoal(pupil_id, goal_category_id, goal_id, created_by, created_at, achieved,
                         achieved_at, description, strategies)
    db.session.add(new_goal)
    db.session.commit()
    return pupilgoal_schema.jsonify(new_goal)

###############################
#- PATCH GOAL * TESTED
###############################

@app.route('/api/goal/<goal_id>', methods=['PATCH'])
@token_required
def put_goal(current_user, goal_id):
    goal = PupilGoal.query.filter_by(goal_id = goal_id).first()
    data = request.get_json()
    for key in data:
        match key:
            case 'created_at':
                goal.created_at = data[key]
            case 'achieved':
                goal.achieved = data[key]
            case 'achieved_at':
                goal.achieved_at = data[key]
            case 'description':
                goal.description = data[key]
            case 'strategies':
                goal.strategies = data[key]
    db.session.commit()
    return pupilgoal_schema.jsonify(goal)

###############################
#- POST GOAL CHECK * TESTED
###############################

@app.route('/api/goal/<goal_id>/check', methods=['POST'])
@token_required
def add_goalcheck(current_user, goal_id):
    this_goal = PupilGoal.query.filter_by(goal_id = goal_id).first()
    this_goal_id = goal_id
    created_by = current_user.name
    created_at = request.json['created_at']
    comment = request.json['comment']
    new_goalcheck = GoalCheck(this_goal_id, created_by, created_at, comment)
    db.session.add(new_goalcheck)
    db.session.commit()
    return pupilgoal_schema.jsonify(this_goal)

###############################
#- PATCH GOAL CHECK * TESTED
###############################
#! TO-DO: IMPLEMENT goal_check_id or pass the id in the schema

@app.route('/api/goal/<goal_id>/check', methods=['PATCH'])
@token_required
def patch_goalcheck(current_user, goal_id):
    goal_check = GoalCheck.query.filter_by(goal_id = goal_id).first()
    data = request.get_json()
    for key in data:
        match key:
            case 'created_at':
                goal_check.created_at = data[key]
            case 'comment':
                goal_check.comment = data[key]
    db.session.commit()
    return goalcheck_schema.jsonify(goal_check)

###############################
#- POST GATEGORY STATE * TESTED
###############################

@app.route('/api/pupil/<internal_id>/categorystatus/<category_id>', methods=['POST'])
@token_required
def add_category_state(current_user, internal_id, category_id):
    this_pupil = Pupil.query.filter_by(internal_id = internal_id).first()
    pupil_id = internal_id
    goal_category_id = category_id
    state = request.json['state']
    created_by = current_user.name
    created_at = request.json['created_at'] 
    created_at = datetime.strptime(created_at, '%Y-%m-%d').date()
    category_status_exists = db.session.query(PupilCategoryStatus).filter(PupilCategoryStatus.pupil_id == internal_id, PupilCategoryStatus.goal_category_id == category_id ).first() is not None
    if category_status_exists == True :
        return jsonify( {"message": "This category status exists already - please update instead!"})
    else:
        new_category_status = PupilCategoryStatus(pupil_id, goal_category_id, state, created_by, created_at)
        db.session.add(new_category_status)
        db.session.commit()
        return pupil_schema.jsonify(this_pupil)

###############################
#- PATCH GATEGORY STATE
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
#- POST LIST WITH ALL PUPILS * TESTED
###############################

@app.route('/api/list/all', methods=['POST'])
@token_required
def add_list_all(current_user):
    
    list_id = str(uuid.uuid4().hex)
    list_name = request.json['list_name']
    list_description = request.json['list_description']
    created_by = current_user.name
    new_list = SchoolList(list_id, list_name, list_description, created_by)
    db.session.add(new_list)
    all_pupils = Pupil.query.all()
    for item in all_pupils:
        origin_list = list_id
        listed_pupil_id = item.internal_id
        pupil_list_status = False
        pupil_list_comment = None
        pupil_list_entry_by = None
        new_pupil_list = PupilList(origin_list, listed_pupil_id, pupil_list_status, pupil_list_comment, pupil_list_entry_by)
        db.session.add(new_pupil_list)
    db.session.commit()    
    return school_list_schema.jsonify(new_list)

###############################
#- POST LIST WITH GROUP OF PUPILS * TESTED
###############################

@app.route('/api/list/group', methods=['POST'])
@token_required
def add_list_group(current_user):
    internal_id_list = request.json['pupils']
    list_id = str(uuid.uuid4().hex)
    list_name = request.json['list_name']
    list_description = request.json['list_description']
    created_by = current_user.name
    new_list = SchoolList(list_id, list_name, list_description, created_by)
    db.session.add(new_list)
    for item in internal_id_list:
        origin_list = list_id
        listed_pupil_id = item
        pupil_list_status = False
        pupil_list_comment = None
        pupil_list_entry_by = None
        new_pupil_list = PupilList(origin_list, listed_pupil_id, pupil_list_status, pupil_list_comment, pupil_list_entry_by)
        db.session.add(new_pupil_list)
    db.session.commit()
    return school_list_schema.jsonify(new_list)

###############################
#- GET ALL LISTS * TESTED
###############################

@app.route('/api/list/all', methods=['GET'])
@token_required
def get_lists(current_user):
    all_lists = SchoolList.query.all()
    result = school_lists_schema.dump(all_lists)
    return jsonify(result)

################################
#- POST PUPIL(S) TO LIST * TESTED
################################

@app.route('/api/list/<list_id>/pupils', methods=['POST'])
@token_required
def add_pupil_to_list(current_user, list_id):
    
    internal_id_list = request.json['pupils']
    for item in internal_id_list:
        school_list = SchoolList.query.filter_by(list_id = list_id).first()
        origin_list = list_id
        listed_pupil_id = item
        pupil_list_status = False
        pupil_list_comment = None
        pupil_list_entry_by = None
        new_pupil_list = PupilList(origin_list, listed_pupil_id, pupil_list_status, pupil_list_comment, pupil_list_entry_by)
        db.session.add(new_pupil_list)
    db.session.commit()
    return school_list_schema.jsonify(school_list)

####################################################################################################################
#-                           #######################################################################################
#-      API SCHOOLDAYS       #######################################################################################
#-                           #######################################################################################
####################################################################################################################

###############################
#- POST SCHOOLDAY * TESTED
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
#- GET ALL SCHOOLDAYS * TESTED
###############################

@app.route('/api/schoolday/all', methods=['GET'])
@token_required
def get_schooldays(current_user):
    all_schooldays = db.session.query(Schoolday).all()
    result = schooldays_schema.dump(all_schooldays)
    return jsonify(result)

###############################
#- GET ONE SCHOOLDAY * TESTED
###############################

@app.route('/api/schoolday/<date>', methods=['GET'])
@token_required
def get_schooday(current_user, date):
    stringtodatetime = datetime.strptime(date, '%Y-%m-%d').date()
    this_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    return schoolday_schema.jsonify(this_schoolday)

###############################
#- DELETE ONE SCHOOLDAY * TESTED
###############################

@app.route('/api/schoolday/<date>', methods=['DELETE'])
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
#- POST MISSED CLASS * TESTED
###############################

@app.route('/api/missedclass', methods=['POST'])
@token_required
def add_missedclass(current_user):
    missed_pupil_id = request.json['missed_pupil_id']
    missed_day = request.json['missed_day']
    stringtodatetime = datetime.strptime(missed_day, '%Y-%m-%d').date()
    this_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    missed_day_id = this_schoolday.id
    missedclass_exists = db.session.query(MissedClass).filter(MissedClass.missed_day_id == missed_day_id, MissedClass.missed_pupil_id == missed_pupil_id ).first() is not None
    if missedclass_exists == True :
        return jsonify( {"message": "This missed class exists already - please update instead!"})
    else:    
        missed_type = request.json['missed_type']
        excused = request.json['excused']
        contacted = request.json['contacted']
        returned = request.json['returned']
        returned_at = request.json['returnedAt']
        late_at = request.json['lateAt']
        written_excuse = request.json['writtenExcuse']
        created_by = current_user.name
        modified_by = None
        new_missedclass = MissedClass(missed_pupil_id, missed_day_id, missed_type, excused,
                                      contacted, returned, written_excuse, late_at, returned_at,
                                      created_by, modified_by)
        db.session.add(new_missedclass)
        db.session.commit()
        return missedclass_schema.jsonify(new_missedclass)

###############################
#- GET ALL MISSED CLASSES * TESTED
###############################

@app.route('/api/missedclass/all', methods=['GET'])
@token_required
def get_missedclasses(current_user):
    all_missedclasses = MissedClass.query.all()
    result = missedclasses_schema.dump(all_missedclasses)
    return jsonify(result)

###############################
#- GET ONE MISSED CLASS * TESTED
###############################

@app.route('/api/missedclass/<id>', methods=['GET'])
@token_required
def get_missedclass(current_user, id):
    this_missedclass = db.session.query(MissedClass).get(id)
    return missedclass_schema.jsonify(this_missedclass)

###############################
#- PATCH MISSED CLASS * TESTED
###############################

@app.route('/api/missedclass/<pupil_id>/<date>', methods=['PATCH'])
@token_required
def update_missedclass(current_user, pupil_id, date):
    stringtodatetime = datetime.strptime(date, '%Y-%m-%d').date()
    missed_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    missed_class = db.session.query(MissedClass).filter(MissedClass.missed_day_id == missed_schoolday.id, MissedClass.missed_pupil_id == pupil_id ).first()
    data = request.get_json()
    for key in data:
        match key:
            case 'missed_type':
                missed_class.missed_type = data[key]
            case 'excused':
                missed_class.excused = data[key]
            case 'contacted':
                missed_class.contacted = data[key]
            case 'returned':
                missed_class.returned = data[key]
            case 'written_excuse':
                missed_class.written_excuse = data[key]
            case 'late_at':
                missed_class.late_at = data[key]
            case 'returned_at':
                missed_class.returned_at = data[key]
            case 'modified_by':
                missed_class.modified_by = data[key]

    db.session.commit()
    return missedclass_schema.jsonify(missed_class)

###############################
#- DELETE MISSED CLASS WITH DATE * TESTED
###############################

@app.route('/api/missedclass/<pupil_id>/<schoolday>', methods=['DELETE'])
@token_required
def delete_missedclass_with_date(current_user, pupil_id, schoolday):
    
    stringtodatetime = datetime.strptime(schoolday, '%Y-%m-%d').date()
    missed_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    thismissed_day_id = missed_schoolday.id
    missed_schoolday = db.session.query(MissedClass).filter(Schoolday.schoolday == stringtodatetime ).first()
    missed_pupil_id = pupil_id
    missedclass = db.session.query(MissedClass).filter(MissedClass.missed_day_id == thismissed_day_id, MissedClass.missed_pupil_id == missed_pupil_id ).first() 
  
    db.session.delete(missedclass)
    db.session.commit()
    return jsonify( {"message": "The missed class was deleted!"})
   
#####################################################################################################################
#-                            #######################################################################################
#-      API ADMONITIONS       #######################################################################################
#-                            #######################################################################################
#####################################################################################################################

###############################
#- POST ADMONITION  * TESTED
###############################

@app.route('/api/admonition', methods=['POST'])
@token_required
def add_admonition(current_user):
    admonishedpupil_id = request.json['admonishedpupil_id']
    admonishedday = request.json['admonished_day']
    stringtodatetime = datetime.strptime(admonishedday, '%Y-%m-%d').date()
    this_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    admonished_day_id = this_schoolday.id
    day_exists = db.session.query(Admonition).filter_by(admonished_day_id = this_schoolday.id).scalar() is not None
    pupil_exists = db.session.query(Admonition).filter_by(admonishedpupil_id = admonishedpupil_id).scalar is not None
    if day_exists == True and pupil_exists == True:
        return jsonify( {"message": "This missed class exists already - please update instead!"})
    else:    
        admonition_type = request.json['admonition_type']
        admonition_reason = request.json['admonition_reason']
        new_admonition = Admonition(admonishedpupil_id, admonished_day_id, admonition_type, admonition_reason)
        db.session.add(new_admonition)
        db.session.commit()
        return admonition_schema.jsonify(new_admonition)

###############################
#- GET ADMONITIONS  * TESTED
###############################

@app.route('/api/admonition/all', methods=['GET'])
@token_required
def get_admonitions(current_user):
    all_admonitions = Admonition.query.all()
    result = pupiladmonitions_schema.dump(all_admonitions)
    return jsonify(result)

###############################
#- GET ONE ADMONITION * TESTED
###############################

@app.route('/api/admonition/<id>', methods=['GET'])
@token_required
def get_admonition(current_user, id):
    this_admonition = db.session.query(Admonition).get(id)
    return pupiladmonition_schema.jsonify(this_admonition)

###############################
#- PATCH ADMONITION
###############################

@app.route('/api/admonition/<id>', methods=['PATCH'])
@token_required
def update_admonition(current_user, id):
    admonition = Admonition.query.get(id)
    data = request.get_json()
    for key in data:
        match key:
            case 'admonition_type': 
                admonition.admonition_type = data[key]
            case 'admonition_reason':
                admonition.admonition_reason = data[key]
    db.session.commit()
    return admonition_schema.jsonify(admonition)

###############################
#- DELETE ADMONITION BY ID
###############################

@app.route('/api/admonition/<id>', methods=['DELETE'])
@token_required
def delete_admonition(current_user, id):
    admonition = db.session.query(Admonition).get(id)
    db.session.delete(admonition)
    db.session.commit()
    return jsonify( {"message": "The admonition was deleted!"})

##########################################
#- DELETE ADMONITION BY PUPIL_ID AND DATE
##########################################

@app.route('/api/admonition/<pupil_id>/<date>', methods=['DELETE'])
@token_required
def delete_admonition_by_day(current_user, pupil_id, date):
    stringtodatetime = datetime.strptime(date, '%Y-%m-%d').date()
    admonished_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    thisadmonished_day_id = admonished_schoolday.id
    missed_pupil_id = pupil_id
    admonition = db.session.query(Admonition).filter(Admonition.admonished_day_id == thisadmonished_day_id, Admonition.admonishedpupil_id == missed_pupil_id ).first() 
    db.session.delete(admonition)
    db.session.commit()
    return jsonify( {"message": "The admonition was deleted!"})

##########################
#- PATCH IMAGE PUPIL AVATAR * TESTED
##########################

@app.route('/api/pupil/<internal_id>/avatar', methods=['PATCH'])
@token_required
def upload_avatar(current_user, internal_id):
    pupil = db.session.query(Pupil).filter(Pupil.internal_id == 
                                                internal_id).first()
    if 'file' not in request.files:
        return jsonify({'error': 'keine Datei vorhanden'}), 400
    file = request.files['file']   
    filename = str(uuid.uuid4().hex) + '.jpg'
    avatar_url = app.config['UPLOAD_FOLDER'] + '/' + filename
    file.save(avatar_url)
    if len(str(pupil.avatar_url)) > 4:
        os.remove(str(pupil.avatar_url))
    pupil.avatar_url = avatar_url
    db.session.commit()
    return jsonify({'msg': 'media uploaded succesfully'})

##########################
#- GET IMAGE PUPIL AVATAR * TESTED
##########################

@app.route('/api/pupil/<internal_id>/avatar', methods=['GET'])
@token_required
def download_avatar(current_user, internal_id):
    pupil = db.session.query(Pupil).filter(Pupil.internal_id == 
                                                internal_id).first()
    url_path = pupil.avatar_url
    return send_file(url_path, mimetype='image/jpg')

#############################
#- CSV IMPORTS * TESTED
#############################
#- from https://gist.github.com/dasdachs/69c42dfcfbf2107399323a4c86cdb791

@app.route('/api/import/categories', methods=['GET', 'POST'])
@token_required
def upload_categories_csv(current_user):
    new_categories = []
    if request.method == 'POST':

        csv_file = request.files['file']
        csv_file = TextIOWrapper(csv_file, encoding='utf-8')
        csv_reader = csv.reader(csv_file, delimiter=';')
        for row in csv_reader:
            #- I'd very much like to jump over the first row to have headings in the csv, now taking them out by hand.
            category = GoalCategory(category_id=row[0],	parent_category=row[1],	category_name=row[2])
            new_categories.append(category)
            db.session.add(category)
        
        db.session.commit()
        return goalcategories_schema.jsonify(new_categories)

@app.route('/api/import/schooldays', methods=['GET', 'POST'])
@token_required
def upload_schooldays_csv(current_user):
    new_schooldays = []
    if request.method == 'POST':

        csv_file = request.files['file']
        csv_file = TextIOWrapper(csv_file, encoding='utf-8')
        csv_reader = csv.reader(csv_file, delimiter=';')
        for row in csv_reader:
            schoolday = Schoolday(schoolday=datetime.strptime(row[0], '%Y-%m-%d').date())
            new_schooldays.append(schoolday)
            db.session.add(schoolday)
        
        db.session.commit()
        return schooldays_schema.jsonify(new_schooldays)

#- Run server

# db.init_app(app) because of https://stackoverflow.com/questions/9692962/flask-sqlalchemy-import-context-issue/9695045#9695045
db.init_app(app)
with app.app_context():
    #db.drop_all()
    db.create_all()
if __name__ == '__main__':
    app.run(debug=True)
