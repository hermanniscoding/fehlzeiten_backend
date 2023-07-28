from copy import error
from flask import Flask, request, jsonify, make_response, send_file
from sqlalchemy.sql import exists
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
from flask_sock import Sock

from pprint import pprint

from io import TextIOWrapper
import csv

from models.pupil import *
from models.schoolday import *
from models.user import *
from models.enums import *

#- Init app

app = Flask(__name__)
sock = Sock(app)
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

class SchooldayOnlySchema(ma.Schema):

    class Meta:
        fields = ('schoolday',)

schoolday_only_schema = SchooldayOnlySchema()
schooldays_only_schema = SchooldayOnlySchema(many = True)

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
#- PUPIL WORKBOOK SCHEMA - CHECKED
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

####################
#- WORKBOOK SCHEMA - CHECKED
####################

class WorkbookSchema(ma.Schema):
    subject = EnumField(SubjectTypeEnum, by_value=False)
    workbookpupils = fields.List(fields.Nested(PupilWorkbookListSchema))
    class Meta:
        fields = ('isbn', 'name', 'subject', 'workbookpupils')

workbook_schema = WorkbookSchema()
workbooks_schema = WorkbookSchema(many=True)

################
#- PUPIL LIST SCHEMA - CHECKED
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

################
#- SCHOOL LIST SCHEMA - CHECKED
################

class SchoolListSchema(ma.Schema):
    pupilsinlist = fields.List(fields.Nested(PupilListSchema))
    
    class Meta:
        fields = ('list_id', 'list_name', 'list_description', 'created_by', 'pupilsinlist')

school_list_schema = SchoolListSchema()
school_lists_schema = SchoolListSchema(many= True)

############################
#- DEVELOPMENT GOAL CHECK SCHEMA - CHECKED
############################

class GoalCheckSchema(ma.Schema):
    class Meta:
        fields = ('id','created_by', 'created_at', 'comment')

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

############################
#- PUPIL CATEGORY STATUS SCHEMA - CHECKED
############################

class PupilCategoryStatusSchema(ma.Schema):
    
    class Meta:
        fields = ('id', 'goal_category_id', 'state')    

pupilcategorystatus_schema = PupilCategoryStatusSchema()
pupilcategorystatuses_schema = PupilCategoryStatusSchema(many= True)

############################
#- GOAL CATEGORY SCHEMA - CHECKED
############################

class GoalCategorySchema(ma.Schema):
    categorygoals = fields.List(fields.Nested(PupilGoalSchema))
    categorystatuses = fields.List(fields.Nested(PupilCategoryStatusSchema))

    class Meta:
        fields = ('category_id', 'category_name', 'categorygoals',
                  'categorystatuses')

goalcategory_schema = GoalCategorySchema()
goalcategories_schema = GoalCategorySchema(many = True)

############################
#- GOAL CATEGORY SCHEMA WITHOUT CHILDREN - CHECKED
############################

class GoalCategoryFlatSchema(ma.Schema):

    class Meta:
        fields = ('category_id', 'category_name', 'parent_category')

goalcategoryflat_schema = GoalCategoryFlatSchema()
goalcategoriesflat_schema = GoalCategoryFlatSchema(many = True)

############################
#- COMPETENCE CHECKS SCHEMA - CHECKED
############################

class CompetenceCheckSchema(ma.Schema):
    class Meta:
        fields = ('check_id', 'created_by', 'created_at', 'competence_status', 'comment', 'file_url', 'pupil_id', 'competence_id')

competence_check_schema = CompetenceCheckSchema()
competence_checks_schema = CompetenceCheckSchema(many=True)

############################
#- COMPETENCE CATEGORIES SCHEMA
############################

class CompetenceSchema(ma.Schema):

    class Meta:
        fields = ('competence_id', 'competence_name')

competence_schema = CompetenceSchema()
competences_schema = CompetenceSchema(many = True)

############################
#- COMPETENCE FLAT SCHEMA
############################

class CompetenceFlatSchema(ma.Schema):

    class Meta:
        fields = ('competence_id', 'parent_competence', 'competence_name')

competence_flat_schema = CompetenceFlatSchema()
competences_flat_schema = CompetenceFlatSchema(many = True)

############################
#- AUTHORIZATION SCHEMA - CHECKED
############################

class AuthorizationSchema(ma.Schema):
    class Meta:
        fields = ('description', 'status', 'pupil_id', 'created_by')

authorization_schema = AuthorizationSchema()
authorizations_schema = AuthorizationSchema(many=True)

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
    competencechecks = fields.List(fields.Nested(CompetenceCheckSchema, exclude=("pupil_id",)))
    authorizations = fields.List(fields.Nested(AuthorizationSchema)) 
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

#- WEBSOCKET
@sock.route('/api/socket')
def websocket(sock):
    if True:
        print('SOCKET: connection started')
    while True:
        data = sock.receive()
        print('SOCKET: Data received:', data)

        #sock.send('SOCKET AUS DEM SERVER ')
# def websocketEmit(sock, data):
#     while True:
#         sock.send(data)
    


##########################################
#-                      ##################
#-      API USERS       ##################
#-                      ##################
##########################################

############
#- GET USERS *CHECKED*
############

@app.route('/api/user/all', methods=['GET'])
@token_required
def get_all_users(current_user):
    if not current_user.admin:
        return jsonify({'warning' : 'Not authorized for this request!'})
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
#- POST USER *CHECKED*
##############

@app.route('/api/user', methods=['POST'])
def create_user():
#! UNCOMMENT THIS BEFORE PRODUCTION!!
# @token_required
# def create_user(current_user):
#     if not current_user.admin:
#         return jsonify({'error' : 'Not authorized!'})

    data = request.get_json()
    if db.session.query(exists().where(User.name == data['name'])).scalar() == True:
        return jsonify({'warning' : 'User already exists!'})  
    is_admin = data['is_admin']
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(public_id=str(uuid.uuid4().hex), name=data['name'],
                     password=hashed_password, admin=is_admin)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message' : 'New user created!'})

#################
#- PUT USER * TESTED
#################

@app.route('/api/user/<public_id>', methods=['PUT'])
@token_required
def promote_user(current_user, public_id):
    if not current_user.admin:
        return jsonify({'warning' : 'Not authorized!'})
    user = User.query.filter_by(public_id=public_id).first()
    if not user:
        return jsonify({'error' : 'No user found!'})
    user.admin = True
    db.session.commit()
    return jsonify({'message' : 'The user has been promoted!'})

####################
#- DELETE USER *CHECKED*
####################

@app.route('/api/user/<public_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, public_id):
    if not current_user.admin:
        return jsonify({'warning' : 'Not authorized!'})
    user = User.query.filter_by(public_id=public_id).first()
    if not user:
        return jsonify({'error' : 'No user found!'})

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message' : 'The user has been deleted!'})
    
#####################
#- GET USER LOGIN *CHECKED*
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
#- POST PUPIL *CHECKED*
###############

@app.route('/api/pupil', methods=['POST'])
@token_required
def add_pupil(current_user):
    data = request.get_json()
    internal_id = data['internal_id']
    exists = db.session.query(Pupil).filter_by(internal_id= internal_id).scalar() is not None 
    if exists == True:
        return jsonify( {"message": "This pupil exists already - please update the page!"})
    else:     
        credit = data['credit']
        ogs = data['ogs']
        five_years = data['five_years']
        individual_development_plan = data['individual_development_plan']
        special_needs = data['special_needs']
        communication_pupil = data['communication_pupil']
        communication_tutor1 = data['communication_tutor1']
        communication_tutor2 = data['communication_tutor2']
        preschool_revision = data['preschool_revision']
        avatar_url = data['avatar_url']
        special_information = data['special_information']
        if data['migration_support_ends'] != None:
            migration_support_ends = datetime.strptime(data['migration_support_ends'], '%Y-%m-%d').date() 
        else:
            migration_support_ends = None
        if data['migration_follow_support_ends'] != None:
            migration_follow_support_ends = datetime.strptime(data['migration_follow_support_ends'], '%Y-%m-%d').date()
        else:
            migration_follow_support_ends = None
        new_pupil = Pupil(internal_id, credit, ogs, individual_development_plan, five_years,
                        special_needs, communication_pupil, communication_tutor1,
                        communication_tutor2, preschool_revision, migration_support_ends,
                        migration_follow_support_ends, avatar_url, special_information)       
        db.session.add(new_pupil)
        db.session.commit()
        response = pupil_schema.jsonify(new_pupil)
        return response

###############
#- PATCH PUPIL *CHECKED*
###############

@app.route('/api/pupil/<internal_id>', methods=['PATCH'])
@token_required
def update_pupil(current_user, internal_id):
    pupil = Pupil.query.filter_by(internal_id = internal_id).first()
    if pupil == None:
        return jsonify({'error': 'This pupil does not exist!'})
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
#- GET ALL PUPILS *CHECKED*
###############################

@app.route('/api/pupil/all', methods=['GET'])
@token_required
def get_pupils(current_user):
    all_pupils = Pupil.query.all()
    if all_pupils == []:
        return jsonify({'error': 'No pupils found!'})
    result = pupils_schema.dump(all_pupils)
    return jsonify(result)

###############################
#- GET PUPILS FROM GIVEN IN ARRAY *CHECKED*
###############################

@app.route('/api/pupil/list', methods=['GET'])
@token_required
def get_given_pupils(current_user):
    internal_id_list = request.json['pupils']
    pupils_list = []
    for item in internal_id_list:
        this_pupil = db.session.query(Pupil).filter(Pupil.internal_id ==
                                                    item).first()
        if this_pupil != None:
            pupils_list.append(this_pupil)
    if pupils_list == []:
        return jsonify({'error': 'None of the given pupils found!'})
    result = pupils_schema.dump(pupils_list)
    return jsonify(result)

###############################
#- GET ONE PUPIL *CHECKED*
###############################

@app.route('/api/pupil/<internal_id>', methods=['GET'])
@token_required
def get_pupil(current_user, internal_id):
    this_pupil = db.session.query(Pupil).filter(Pupil.internal_id == 
                                                internal_id).first()
    if this_pupil == None:
        return jsonify({'error': 'This pupil does not exist!'})
    return pupil_schema.jsonify(this_pupil)

###############################
#- DELETE PUPIL *CHECKED*
###############################

@app.route('/api/pupil/<internal_id>', methods=['DELETE'])
@token_required
def delete_pupil(current_user, internal_id):
    pupil = Pupil.query.filter_by(internal_id = internal_id).first()
    if pupil == None:
        return jsonify( {"error": "The pupil does not exist!"})
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
#- GET WORKBOOKS *CHECKED*
###############################

@app.route('/api/workbook/all', methods=['GET'])
@token_required
def get_workbooks(current_user):
    all_workbooks = Workbook.query.all()
    if all_workbooks == []:
        return jsonify({'error': 'No workbooks found!'})
    result = workbooks_schema.dump(all_workbooks)
    return jsonify(result)

###############################
#- POST WORKBOOK *CHECKED*
###############################

@app.route('/api/workbook/new', methods=['POST'])
@token_required
def create_workbook(current_user):
    isbn = request.json['isbn']
    name = request.json['name']
    subject = request.json['subject']
    if db.session.query(Workbook).filter_by(isbn= isbn).scalar() is not None:
        return jsonify({"error": "This workbook already exists!"})
    if subject not in subject_enums:
        return jsonify({"error": "This subject does not exist!"})
    new_workbook = Workbook(isbn, name, subject)
    db.session.add(new_workbook)
    db.session.commit()
    return workbook_schema.jsonify(new_workbook)

###############################
#- DELETE WORKBOOK *CHECKED*
###############################

@app.route('/api/workbook/<isbn>', methods=['DELETE'])
@token_required
def delete_workbook(current_user, isbn):
    this_workbook = Workbook.query.filter_by(isbn = isbn).first()
    if this_workbook == None:
        return jsonify({'error': 'This workbook does not exist!'})
    db.session.delete(this_workbook)
    db.session.commit()
    return jsonify( {"message": "Workbook deleted!"})

###############################
#- POST PUPIL WORKBOOK *CHECKED*
###############################

@app.route('/api/pupil/<internal_id>/workbook/<isbn>', methods=['POST'])
@token_required
def add_workbook_to_pupil(current_user, internal_id, isbn):
    this_pupil = Pupil.query.filter_by(internal_id = internal_id).first()
    if this_pupil == None:
        return jsonify({'error': 'This pupil does not exist!'})
    pupil_id = internal_id
    this_workbook = Workbook.query.filter_by(isbn = isbn).first()
    if this_workbook == None:
        return jsonify({'error': 'This workbook does not exist!'})    
    isbn = isbn
    if db.session.query(exists().where(PupilWorkbook.workbook_isbn == isbn and PupilWorkbook.pupil_id == internal_id)).scalar() == True:
        return jsonify({'error': 'This pupil workbook exists already!'})    
    state = 'active'
    created_by = current_user.name
    created_at = datetime.now().date()
    
    new_pupil_workbook = PupilWorkbook(pupil_id, isbn, state, created_by, created_at)
    db.session.add(new_pupil_workbook)
    db.session.commit()
    return pupil_workbook_schema.jsonify(new_pupil_workbook)

###############################
#- PATCH PUPIL WORKBOOK  *CHECKED*
###############################

@app.route('/api/pupil/<internal_id>/workbook/<isbn>', methods=['PATCH'])
@token_required
def update_PupilWorkbook(current_user, internal_id, isbn):
    pupil_workbook = PupilWorkbook.query.filter_by(pupil_id = internal_id,
                                                  workbook_isbn = isbn).first()
    if pupil_workbook == None:
        return jsonify({'error': 'This pupil workbook does not exist!'})
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
#- GET CATEGORIES *CHECKED*
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
    if all_categories == []:
        return jsonify({'error': 'No categories found!'})
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
#- GET CATEGORIES FLAT JSON *CHECKED*
###############################

@app.route('/api/goalcategories/flat', methods=['GET'])
@token_required
def get_flat_categories(current_user):
    all_categories = GoalCategory.query.all()
    if all_categories == None:
        return jsonify({'error': 'No categories found!'})
    result = goalcategoriesflat_schema.dump(all_categories)
    return jsonify(result)    

###############################
#- POST GOAL *CHECKED*
###############################

@app.route('/api/pupil/<internal_id>/goal', methods=['POST'])
@token_required
def add_goal(current_user, internal_id):
    data = request.get_json()
    pupil = Pupil.query.filter_by(internal_id = internal_id).first()
    if pupil == None:
        return jsonify({'error': 'This pupil does not exist!'})
    pupil_id = pupil.internal_id
    goal_category_id = data['goal_category_id']
    goal_category = db.session.query(GoalCategory).filter_by(category_id = goal_category_id).scalar()
    if goal_category == None:
        return jsonify({'error': 'This category does not exist!'})
    goal_id = str(uuid.uuid4().hex)
    created_by = current_user.name
    created_at = data['created_at']
    achieved = data['achieved']
    achieved_at = data['achieved_at']
    description = data['description']
    strategies = data['strategies']
    new_goal = PupilGoal(pupil_id, goal_category_id, goal_id, created_by, created_at, achieved,
                         achieved_at, description, strategies)
    db.session.add(new_goal)
    db.session.commit()
    return pupilgoal_schema.jsonify(new_goal)

###############################
#- PATCH GOAL *CHECKED*
###############################

@app.route('/api/goal/<goal_id>', methods=['PATCH'])
@token_required
def put_goal(current_user, goal_id):
    goal = PupilGoal.query.filter_by(goal_id = goal_id).first()
    if goal == None:
        return jsonify({'error': 'This goal does not exist!'})
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
#- POST GOAL CHECK *CHECKED*
###############################

@app.route('/api/goal/<goal_id>/check', methods=['POST'])
@token_required
def add_goalcheck(current_user, goal_id):
    this_goal = PupilGoal.query.filter_by(goal_id = goal_id).first()
    if this_goal == None:
        return jsonify({'error': 'This goal does not exist!'})
    this_goal_id = goal_id
    created_by = current_user.name
    created_at = request.json['created_at']
    comment = request.json['comment']
    new_goalcheck = GoalCheck(this_goal_id, created_by, created_at, comment)
    db.session.add(new_goalcheck)
    db.session.commit()
    return pupilgoal_schema.jsonify(this_goal)

###############################
#- PATCH GOAL CHECK *CHECKED*
###############################

@app.route('/api/goal/<goal_id>/check/<check_id>', methods=['PATCH'])
@token_required
def patch_goalcheck(current_user, goal_id, check_id):
    goal_check = GoalCheck.query.filter_by(goal_id = goal_id, id = check_id).first()
    if goal_check == None:
        return jsonify({'error': 'This goal check does not exist!'})
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
#- POST GATEGORY STATE *CHECKED*
###############################

@app.route('/api/pupil/<internal_id>/categorystatus/<category_id>', methods=['POST'])
@token_required
def add_category_state(current_user, internal_id, category_id):
    this_pupil = Pupil.query.filter_by(internal_id = internal_id).first()
    if this_pupil == None:
        return jsonify({'error': 'Pupil does not exist!'})
    pupil_id = internal_id
    this_category = GoalCategory.query.filter_by(category_id = category_id).first()
    if this_category == None:
        return jsonify({'error': 'Category does not exist!'})
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
#- PATCH GATEGORY STATE *CHECKED*
###############################

@app.route('/api/pupil/<internal_id>/categorystatus/<category_id>', methods=['PATCH'])
@token_required
def put_category_state(current_user, internal_id, category_id):
    this_pupil = Pupil.query.filter_by(internal_id = internal_id).first()
    if this_pupil == None:
        return jsonify({'error': 'This pupil does not exist!'})
    this_category = GoalCategory.query.filter_by(category_id = category_id).first()
    if this_category == None:
        return jsonify({'error': 'This category does not exist!'})
    status = PupilCategoryStatus.query.filter_by(pupil_id = internal_id, goal_category_id = category_id).first()
    if status == None:
        return jsonify({'error': 'This category status does not exist!'})
    data = request.get_json()
    for key in data:
        match key:
            case 'state':
                status.state = data['state']
            case 'created_at':
                status.created_at = data['created_at']
    db.session.commit()
    return goalcategory_schema.jsonify(this_category)

###############################################
#-                          ###################
#-   API COMPETENCES        ###################
#-                          ###################
###############################################

###############################
#- GET COMPETENCEs *CHECKED*
###############################

@app.route('/api/competence/all', methods=['GET'])
@token_required
def get_competences(current_user):
    root = {
        "competence_id": 0,
        "competence_name": "competences",
        "subcompetences": [],
    }
    dict = {0: root}
    all_competences = Competence.query.all()
    for item in all_competences:
        dict[item.competence_id] = current = {
            "competence_id": item.competence_id,
            "parent_competence": item.parent_competence,
            "competence_name": item.competence_name,
            "subcompetences": [],
        }
        # Adds actual category to the subcategories list of the parent
        parent = dict.get(item.parent_competence, root)
        parent["subcompetences"].append(current)

    return jsonify(root)

###############################
#- GET CATEGORIES FLAT JSON *CHECKED*
###############################

@app.route('/api/competence/all/flat', methods=['GET'])
@token_required
def get_flat_competences(current_user):
    all_competences = Competence.query.all()
    if all_competences == None:
        return jsonify({'error': 'No competences found!'})
    result = competences_flat_schema.dump(all_competences)
    return jsonify(result)    


###############################
#- POST COMPETENCE CHECK
###############################

@app.route('/api/pupil/<internal_id>/competence/check', methods=['POST'])
@token_required
def add_competence_check(current_user, internal_id):
    pupil = Pupil.query.filter_by(internal_id = internal_id).first()
    pupil_id = pupil.internal_id
    competence_id = request.json['competence_id']
    check_id = str(uuid.uuid4().hex)
    created_by = current_user.name
    created_at = request.json['created_at']
    competence_status = request.json['competence_status']
    comment = request.json['comment']
    file_url = None
    
    new_competence_check = CompetenceCheck(pupil_id, competence_id,
                                           check_id, created_by, created_at,
                                           competence_status, comment, file_url)
    db.session.add(new_competence_check)
    db.session.commit()
    return competence_check_schema.jsonify(new_competence_check)

###############################
#- PATCH COMPETENCE CHECK WITH IMAGE
###############################

@app.route('/api/competence/check/<check_id>', methods=['PATCH'])
@token_required
def upload_competence_image(current_user, check_id):
    competence_check = CompetenceCheck.query.filter_by(check_id = check_id).first()
    
    if 'file' not in request.files:
        return jsonify({'error': 'keine Datei vorhanden'}), 400
    file = request.files['file']   
    filename = str(uuid.uuid4().hex) + '.jpg'
    image_url = app.config['UPLOAD_FOLDER'] + '/' + filename
    file.save(image_url)
    if len(str(competence_check.image_url)) > 4:
        os.remove(str(competence_check.image_url))
    competence_check.image_url = image_url
    db.session.commit()
    return jsonify({'message': 'media uploaded succesfully'})

##########################
#- GET COMPETENCE CHECK IMAGE 
##########################

@app.route('/api/pupil/competence/<check_id>/image', methods=['GET'])
@token_required
def download_competence_image(current_user, check_id):
    competence_check = CompetenceCheck.query.filter_by(check_id = check_id).first()
    url_path = competence_check.image_url
    return send_file(url_path, mimetype='image/jpg')

####################
#- DELETE COMPETENCE CHECK
####################

@app.route('/competence_check/<check_id>', methods=['DELETE'])
@token_required
def delete_competence_check(current_user, check_id):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})

    competence_check = CompetenceCheck.query.filter_by(check_id = check_id).first()
    if not competence_check:
        return jsonify({'message' : 'Competence check does not exist!'})
    db.session.delete(competence_check)
    db.session.commit()

    return jsonify({'message' : 'The competence check has been deleted!'})
    
###################################################################################################################
#-                          #######################################################################################
#-        API LISTS         #######################################################################################
#-                          #######################################################################################
###################################################################################################################

###############################
#- POST LIST WITH ALL PUPILS *CHECKED*
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
#- POST LIST WITH GROUP OF PUPILS *CHECKED*
###############################

@app.route('/api/list/group', methods=['POST'])
@token_required
def add_list_group(current_user):
    this_list_name = request.json['list_name']
    if db.session.query(exists().where(SchoolList.list_name == this_list_name)).scalar() == True:
        return jsonify({'message': 'List already exists!'})
    internal_id_list = request.json['pupils']
    list_id = str(uuid.uuid4().hex)
    list_description = request.json['list_description']
    created_by = current_user.name
    new_list = SchoolList(list_id, this_list_name, list_description, created_by)
    db.session.add(new_list)
    #-We have to create the list to populate it with pupils.
    #-This is why it is created even if pupils are wrong and the list remains empty. 
    for item in internal_id_list:
        if db.session.query(exists().where(Pupil.internal_id == item)).scalar() == True:
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
#- GET ALL LISTS *CHECKED*
###############################

@app.route('/api/list/all', methods=['GET'])
@token_required
def get_lists(current_user):
    all_lists = SchoolList.query.all()
    if all_lists == []:
        return jsonify({'error': 'There are no lists!'})
    result = school_lists_schema.dump(all_lists)
    return jsonify(result)

################################
#- POST PUPIL(S) TO LIST *CHECKED*
################################

@app.route('/api/list/<list_id>/pupils', methods=['POST'])
@token_required
def add_pupil_to_list(current_user, list_id):
    school_list = SchoolList.query.filter_by(list_id = list_id).first()
    if school_list == None:
        return jsonify({'error': 'This list does not exist!'})
    internal_id_list = request.json['pupils']
    if internal_id_list == []:
        return jsonify({'error': 'No pupils found to add to list!'})
    for item in internal_id_list:        
        if Pupil.query.filter_by(internal_id = item).first() != None:
            if PupilList.query.filter_by(origin_list= list_id, listed_pupil_id= item).first() == None:
                origin_list = list_id
                listed_pupil_id = item
                pupil_list_status = False
                pupil_list_comment = None
                pupil_list_entry_by = None
                new_pupil_list = PupilList(origin_list, listed_pupil_id, pupil_list_status, pupil_list_comment, pupil_list_entry_by)
                db.session.add(new_pupil_list)
    db.session.commit()
    return school_list_schema.jsonify(school_list)

###############################
#- DELETE LIST *CHECKED*
###############################

@app.route('/api/list/<list_id>', methods=['DELETE'])
@token_required
def delete_list(current_user, list_id):
    this_list_id = list_id
    this_list = db.session.query(SchoolList).filter(SchoolList.list_id == this_list_id).first()
    if this_list == None:
        return jsonify( {"error": "The school list does not exist!"})
    db.session.delete(this_list)
    db.session.commit()
    return jsonify( {"message": "The school list was deleted!"})


####################################################################################################################
#-                           #######################################################################################
#-      API SCHOOLDAYS       #######################################################################################
#-                           #######################################################################################
####################################################################################################################

###############################
#- POST SCHOOLDAY *CHECKED*
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
#- GET ALL SCHOOLDAYS *CHECKED*
###############################

@app.route('/api/schoolday/all', methods=['GET'])
@token_required
def get_schooldays(current_user):
    all_schooldays = db.session.query(Schoolday).all()
    if all_schooldays == []:
        return jsonify({'error': 'No schooldays found!'})    
    result = schooldays_schema.dump(all_schooldays)
    return jsonify(result)

###############################
#- GET ALL SCHOOLDAYS WITHOUT CHILDREN *CHECKED*
###############################

@app.route('/api/schoolday/only', methods=['GET'])
@token_required
def get_schooldays_only(current_user):
    all_schooldays = db.session.query(Schoolday).all()
    if all_schooldays == []:
        return jsonify({'error': 'No schooldays found!'})
    result = schooldays_only_schema.dump(all_schooldays)
    return jsonify(result)
###############################
#- GET ONE SCHOOLDAY WITH CHILDREN *CHECKED*
###############################

@app.route('/api/schoolday/<date>', methods=['GET'])
@token_required
def get_schooday(current_user, date):
    stringtodatetime = datetime.strptime(date, '%Y-%m-%d').date()
    #- If date has wrong format and strptime fails, we're screwed :-/
    this_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    if this_schoolday == None:
        return jsonify({'error': 'This schoolday does not exist!'})
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
#- POST MISSED CLASS *CHECKED*
###############################

@app.route('/api/missedclass', methods=['POST'])
@token_required
def add_missedclass(current_user):
    missed_pupil_id = request.json['missed_pupil_id']
    if db.session.query(exists().where(Pupil.internal_id == missed_pupil_id)).scalar() != True:
        return jsonify( {"error": "This pupil does not exist!"})
    missed_day = request.json['missed_day']
    stringtodatetime = datetime.strptime(missed_day, '%Y-%m-%d').date()
    this_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    if this_schoolday == None:
        return jsonify( {"error": "This schoolday does not exist!"})
    missed_day_id = this_schoolday.id
    missedclass_exists = db.session.query(MissedClass).filter(MissedClass.missed_day_id == missed_day_id, MissedClass.missed_pupil_id == missed_pupil_id ).first() is not None
    if missedclass_exists == True :
        return jsonify( {"error": "This missed class exists already - please update instead!"})
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
#- GET ALL MISSED CLASSES *CHECKED*
###############################

@app.route('/api/missedclass/all', methods=['GET'])
@token_required
def get_missedclasses(current_user):
    all_missedclasses = MissedClass.query.all()
    if all_missedclasses == []:
        return jsonify({'error': 'There are no missed classes!'})
    result = missedclasses_schema.dump(all_missedclasses)
    return jsonify(result)

###############################
#- GET ONE MISSED CLASS *CHECKED*
###############################

@app.route('/api/missedclass/<id>', methods=['GET'])
@token_required
def get_missedclass(current_user, id):
    this_missedclass = db.session.query(MissedClass).get(id)
    if this_missedclass == None:
        return jsonify({'error': 'This missed class does not exist!'})

    return missedclass_schema.jsonify(this_missedclass)

###############################
#- PATCH MISSED CLASS *CHECKED*
###############################

@app.route('/api/missedclass/<pupil_id>/<date>', methods=['PATCH'])
@token_required
def update_missedclass(current_user, pupil_id, date):
    date_as_datetime = datetime.strptime(date, '%Y-%m-%d').date()
    missed_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == date_as_datetime ).first()
    if missed_schoolday == None:
        return jsonify({'error': 'This schoolday does not exist!'})
    missed_class = db.session.query(MissedClass).filter(MissedClass.missed_day_id == missed_schoolday.id and MissedClass.missed_pupil_id == pupil_id ).first()
    if missed_class == None:
        return jsonify({'error': 'This missed class does not exist!'})
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
#- POST ADMONITION  *CHECKED*
###############################

@app.route('/api/admonition', methods=['POST'])
@token_required
def add_admonition(current_user):
    admonishedpupil_id = request.json['admonishedpupil_id']
    if db.session.query(exists().where(Pupil.internal_id == admonishedpupil_id)).scalar() == False:
        return jsonify( {"error": "This pupil does not exist!"})
    admonishedday = request.json['admonished_day']
    stringtodatetime = datetime.strptime(admonishedday, '%Y-%m-%d').date()
    this_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    if this_schoolday == None:
        return jsonify( {"error": "This schoolday does not exist!"})
    admonished_day_id = this_schoolday.id
    day_exists = db.session.query(Admonition).filter_by(admonished_day_id = this_schoolday.id).scalar() is not None
    pupil_exists = db.session.query(Admonition).filter_by(admonishedpupil_id = admonishedpupil_id).scalar is not None
    
    if day_exists == True and pupil_exists == True:
        return jsonify( {"error": "This missed class exists already - please update instead!"})
    else:    
        admonition_type = request.json['admonition_type']
        admonition_reason = request.json['admonition_reason']
        new_admonition = Admonition(admonishedpupil_id, admonished_day_id, admonition_type, admonition_reason)
        db.session.add(new_admonition)
        db.session.commit()
        return admonition_schema.jsonify(new_admonition)

###############################
#- GET ADMONITIONS  *CHECKED*
###############################

@app.route('/api/admonition/all', methods=['GET'])
@token_required
def get_admonitions(current_user):
    all_admonitions = Admonition.query.all()
    if all_admonitions == []:
        return jsonify({'warning': 'No admonitions found!'})
    result = pupiladmonitions_schema.dump(all_admonitions)
    return jsonify(result)

###############################
#- GET ONE ADMONITION *CHECKED*
###############################

@app.route('/api/admonition/<id>', methods=['GET'])
@token_required
def get_admonition(current_user, id):
    this_admonition = db.session.query(Admonition).get(id)
    if this_admonition == None:
        return jsonify({'error': 'This admonition does not exist!'})

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
#- PATCH IMAGE PUPIL AVATAR *CHECKED*
##########################

@app.route('/api/pupil/<internal_id>/avatar', methods=['PATCH'])
@token_required
def upload_avatar(current_user, internal_id):
    pupil = db.session.query(Pupil).filter(Pupil.internal_id == 
                                                internal_id).first()
    if pupil == None:
        return jsonify({'error': 'This pupil does not exist!'})
    if 'file' not in request.files:
        return jsonify({'error': 'No file attached!'}), 400
    file = request.files['file']   
    filename = str(uuid.uuid4().hex) + '.jpg'
    avatar_url = app.config['UPLOAD_FOLDER'] + '/' + filename
    file.save(avatar_url)
    if len(str(pupil.avatar_url)) > 4:
        os.remove(str(pupil.avatar_url))
    pupil.avatar_url = avatar_url
    db.session.commit()
    return jsonify({'message': 'Media uploaded succesfully!'})

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
#- CSV IMPORTS 
## from https://gist.github.com/dasdachs/69c42dfcfbf2107399323a4c86cdb791

##########################
#- IMPORT CATEGORIES *CHECKED*
##########################

@app.route('/api/import/categories', methods=['POST'])
@token_required
def upload_categories_csv(current_user):
    new_categories = []
    if request.method == 'POST':

        csv_file = request.files['file']
        csv_file = TextIOWrapper(csv_file, encoding='utf-8')
        csv_reader = csv.reader(csv_file, delimiter=';')
        for row in csv_reader:
            #- I'd very much like to jump over the first row to have headings in the csv, now taking them out by hand.
                if db.session.query(exists().where(GoalCategory.category_id == row[0])).scalar() == False:
                    category = GoalCategory(category_id=row[0],	parent_category=row[1],	category_name=row[2])
                    new_categories.append(category)
                    db.session.add(category)
                if new_categories == []:
                    return jsonify({'message': 'No new items!'})
            
        db.session.commit()
        return goalcategories_schema.jsonify(new_categories)

##########################
#- IMPORT COMPETENCES *CHECKED*
##########################

@app.route('/api/import/competences', methods=['POST'])
@token_required
def upload_competences_csv(current_user):
    new_competences = []
    if request.method == 'POST':

        csv_file = request.files['file']
        csv_file = TextIOWrapper(csv_file, encoding='utf-8')
        csv_reader = csv.reader(csv_file, delimiter=';', skipinitialspace= True)
        for row in csv_reader:
            #- I'd very much like to jump over the first row to have headings in the csv, now taking them out by hand.
            if db.session.query(exists().where(Competence.competence_id == row[0])).scalar() == False:
                competence = Competence(competence_id=row[0],	parent_competence=row[1],	competence_name=row[2])
                new_competences.append(competence)
            if new_competences == []:
                return jsonify({'message': 'No new items!'})

            db.session.add(competence)
        
        db.session.commit()
        return competences_schema.jsonify(new_competences)

########################
#- GET IMPORT SCHOOLDAYS *CHECKED*
########################
@app.route('/api/import/schooldays', methods=['GET', 'POST'])
@token_required
def upload_schooldays_csv(current_user):
    new_schooldays = []
    if request.method == 'POST':

        csv_file = request.files['file']
        csv_file = TextIOWrapper(csv_file, encoding='utf-8')
        csv_reader = csv.reader(csv_file, delimiter=';')
        for row in csv_reader:
            #- I'd very much like to jump over the first row to have headings in the csv, now taking them out by hand.
                if db.session.query(exists().where(Schoolday.schoolday == datetime.strptime(row[0], '%Y-%m-%d').date())).scalar() == False:
                    schoolday = Schoolday(schoolday=datetime.strptime(row[0], '%Y-%m-%d').date())
                    new_schooldays.append(schoolday)
                    db.session.add(schoolday)
                if new_schooldays == []:
                    return jsonify({'message': 'No new items!'})        
        db.session.commit()
        return schooldays_schema.jsonify(new_schooldays)

#- Run server

# db.init_app(app) because of https://stackoverflow.com/questions/9692962/flask-sqlalchemy-import-context-issue/9695045#9695045
db.init_app(app)
with app.app_context():
    # db.drop_all()
    db.create_all()
if __name__ == '__main__':
    app.run(debug=True)
