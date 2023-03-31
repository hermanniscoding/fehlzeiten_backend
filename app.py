# from https://www.youtube.com/watch?v=PTZiDnuC86g
# JWT from https://www.youtube.com/watch?v=WxGBoY5iNXY
from copy import error
import enum
import re
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import Schema, fields
from marshmallow.decorators import pre_load
from marshmallow_enum import EnumField
from datetime import datetime, timedelta
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from sqlalchemy.orm import backref
from functools import wraps

# Init app

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# TO-DO: implement socketio like in https://www.youtube.com/watch?v=FIBgDYA-Fas and in https://stackoverflow.com/questions/32545634/flask-a-restful-api-and-socketio-server

# Database
app.config['SECRET_KEY'] = 'THISISNOTTHEREALSECRETKEY'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init db

db = SQLAlchemy(app)
ma = Marshmallow(app)

##########
# MODELS #
##########

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

class CoronaStatusEnum(enum.Enum):
    index = 'index'
    quarantine = 'quarantine'

class MissedTypeEnum(enum.Enum):
    missed = 'missed'
    late = 'late'
    distance = 'distance'

class AdmonitionTypeEnum(enum.Enum):
    yellow = 'yellow'
    red = 'red'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean)

class Schoolday(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    schoolday = db.Column(db.Date, nullable = False)
    missedclasses = db.relationship('MissedClass', backref='schoolday', cascade="all, delete-orphan")
    admonitions = db.relationship('Admonition', backref='schoolday', cascade="all, delete-orphan")

    def __init__(self, schoolday):
        self.schoolday = schoolday

class Hermannpupil(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    group = db.Column(
        db.Enum(GroupEnum),
        nullable = False
    )
    schoolyear = db.Column(
        db.Enum(SchoolyearEnum),
        nullable = False
    )
    credit = db.Column(db.Integer, default = 0)
    ogs = db.Column(db.Boolean)
    pupilmissedclasses = db.relationship('MissedClass', backref='onemissedpupil', cascade="all, delete-orphan")
    pupiladmonitions = db.relationship('Admonition', backref='admonishedpupil', cascade="all, delete-orphan")

    def __init__(self, name, group, schoolyear, credit, ogs):
        self.name = name
        self.group = group
        self. schoolyear = schoolyear
        self.credit = credit
        self.ogs = ogs

class CoronaStatus(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    coronapupil_id = db.Column(db.Integer, db.ForeignKey('hermannpupil.id'))
    untildate = db.Column(db.Date, nullable = True)
    corona_status = db.Column(
        db.Enum(CoronaStatusEnum),
        nullable = False
    )

    def __init__(self, coronapupil_id, corona_status, untildate):
        self.coronapupil_id = coronapupil_id
        self.untildate = untildate
        self.corona_status = corona_status
        

class MissedClass(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    missedpupil_id = db.Column(db.Integer, db.ForeignKey('hermannpupil.id'))
  #  missedpupil = db.relationship('Hermannpupil', uselist=False, lazy='select')
    missedday_id= db.Column(db.Integer, db.ForeignKey('schoolday.id'))
  #  missedday = db.relationship('Schoolday', uselist=False, lazy='select')
    missedtype = db.Column(
        db.Enum(MissedTypeEnum),
        nullable = False
    )
    excused = db.Column(db.Boolean)
    contacted = db.Column(db.Boolean)

    def __init__(self, missedpupil_id, missedday_id, missedtype, excused, contacted):
        self.missedpupil_id = missedpupil_id
        self.missedday_id = missedday_id
        self.missedtype = missedtype
        self.excused = excused
        self.contacted = contacted

class Admonition(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    admonishedpupil_id = db.Column('admonishedpupil', db.Integer, db.ForeignKey('hermannpupil.id'))
    admonishedday_id = db.Column('admonishedday', db.Integer, db.ForeignKey('schoolday.id'))
    admonitiontype = db.Column(db.Enum(AdmonitionTypeEnum),
    nullable = False
    )
    admonitionreason = db.Column(db.String(200), nullable = False)

    def __init__(self, admonishedpupil_id, admonishedday_id, admonitiontype, admonitionreason):
        self.admonishedpupil_id = admonishedpupil_id
        self.admonishedday_id = admonishedday_id
        self.admonitiontype = admonitiontype
        self.admonitionreason = admonitionreason



###################
# SCHEMA AND INIT #
###################

class CoronaStatusSchema(ma.Schema):
    corona_status = EnumField(CoronaStatusEnum, by_value=False)
    class Meta:
        fields = ('coronapupil_id', 'corona_status', 'untildate')
coronastatus_schema = CoronaStatusSchema()
coronastatuses_schema = CoronaStatusSchema(many=True)

# Admonition

class AdmonitionSchema(ma.Schema):
    admonitiontype = EnumField(AdmonitionTypeEnum, by_value=False)
    class Meta:
        fields = ('admonishedpupil_id', 'admonishedday_id', 'admonitiontype', 'admonitionreason')

admonition_schema = AdmonitionSchema()
admonitions_schema = AdmonitionSchema(many = True)

# MissedClass

class MissedClassSchema(ma.Schema):
    include_fk = True
    missedtype = EnumField(MissedTypeEnum, by_value=False)
    # missedpupil = ma.Function(lambda obj: obj.hermanpupil.name)
    class Meta:
        fields = ('missedpupil_id', 'missedday_id', 'missedtype', 'excused', 'contacted')

missedclass_schema = MissedClassSchema()
missedclasses_schema = MissedClassSchema(many = True)

# Schoolday

class SchooldaySchema(ma.Schema):
    missedclasses = fields.List(fields.Nested(MissedClassSchema, exclude=("missedday_id",)))
    admonitions = fields.List(fields.Nested(AdmonitionSchema, exclude=("admonishedday_id",)))
    class Meta:
        fields = ('schoolday', 'missedclasses', 'admonitions')

schoolday_schema = SchooldaySchema()
schooldays_schema = SchooldaySchema(many = True)

class PupilMissedClassSchema(ma.Schema):
    missedtype = EnumField(MissedTypeEnum, by_value=False)
    missed_schoolday = ma.Function(lambda obj:obj.schoolday.schoolday.isoformat())
    # missed_day = missed_schoolday.strftime('%Y-%m-%d')
    class Meta:
        fields = ('missedpupil_id', 'missed_schoolday', 'missedtype', 'excused', 'contacted')

pupilmissedclass_schema = PupilMissedClassSchema()
pupilmissedclasses_schema = PupilMissedClassSchema(many = True)

class PupilAdmonitionSchema(ma.Schema):
    admonitiontype = EnumField(AdmonitionTypeEnum, by_value=False)
    admonished_schoolday = ma.Function(lambda obj:obj.schoolday.schoolday.isoformat())
    class Meta:
        fields = ('admonishedpupil_id', 'admonished_schoolday', 'admonitiontype', 'admonitionreason')

pupiladmonition_schema = PupilAdmonitionSchema()
pupiladmonitions_schema = PupilAdmonitionSchema(many = True)

# Hermannpupil 

class HermannpupilSchema(ma.Schema):
    group = EnumField(GroupEnum, by_value=False)
    schoolyear = EnumField(SchoolyearEnum, by_value=False)
    pupilmissedclasses = fields.List(fields.Nested(PupilMissedClassSchema, exclude=("missedpupil_id",)))
    pupiladmonitions = fields.List(fields.Nested(PupilAdmonitionSchema, exclude=("admonishedpupil_id",)))
    class Meta:
        fields = ('id', 'name', 'group', 'schoolyear', 'credit', 'ogs', 'pupilmissedclasses', 'pupiladmonitions')

hermannpupil_schema = HermannpupilSchema()
hermannpupils_schema = HermannpupilSchema(many = True)

###############
# CRUD ROUTES #
###############

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
    
# Get users

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

# Create user

@app.route('/api/user', methods=['POST'])
@token_required
def create_user(current_user):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'})

    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(public_id=str(uuid.uuid4()), name=data['name'], password=hashed_password, admin=False)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message' : 'New user created!'})

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

# Delete user

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
    
# Login

@app.route('/api/login')
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 402, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    user = User.query.filter_by(name=auth.username).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'public_id' : user.public_id, 'exp' : datetime.utcnow() + timedelta(hours=120)}, app.config['SECRET_KEY'])

        return jsonify({'token' : token.decode('UTF-8')})

    return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

# Create a Hermannpupil

@app.route('/api/hermannkind', methods=['POST'])
@token_required
def add_hermannpupil(current_user):
    name = request.json['name']
    group = request.json['group']
    schoolyear = request.json['schoolyear']
    credit = request.json['credit']
    ogs = request.json['ogs']

    new_hermannpupil = Hermannpupil(name, group, schoolyear, credit, ogs)
    
    db.session.add(new_hermannpupil)
    db.session.commit()
    return hermannpupil_schema.jsonify(new_hermannpupil)

# Bulk create Hermannpupils
# https://stackoverflow.com/questions/60261701/sqlalchemy-insert-from-a-json-list-to-database

# Update a Hermannpupil

@app.route('/api/hermannkind/<id>', methods=['PATCH'])
@token_required
def update_hermannpupil(current_user, id):
    hermannpupil = Hermannpupil.query.get(id)
    hermannpupil.name = request.json['name']
    hermannpupil.group = request.json['group']
    hermannpupil.schoolyear = request.json['schoolyear']
    hermannpupil.credit = request.json['credit']
    hermannpupil.ogs = request.json['ogs']
    db.session.commit()
    return hermannpupil_schema.jsonify(hermannpupil)

# update the Hermannpupil's credit

@app.route('/api/hermannkind/<id>/credit', methods=['PATCH'])
@token_required
def update_hermannpupilcredit(current_user, id):
    hermannpupil = Hermannpupil.query.get(id)
    hermannpupil.credit = request.json['credit']
    db.session.commit()
    return hermannpupil_schema.jsonify(hermannpupil)

# update the Hermannpupil's OGS status

@app.route('/api/hermannkind/<id>/ogs', methods=['PATCH'])
@token_required
def update_hermannpupilogsstatus(current_user, id):
    hermannpupil = Hermannpupil.query.get(id)
    hermannpupil.ogs = request.json['ogs']
    db.session.commit()
    return hermannpupil_schema.jsonify(hermannpupil)

# delete a Hermannpupil

@app.route('/api/hermannkind/<id>', methods=['DELETE'])
@token_required
def delete_hermannpupil(current_user, id):
    hermannpupil = Hermannpupil.query.get(id)
    db.session.delete(hermannpupil)
    db.session.commit()
    return jsonify( {"message": "The hermannpupil was deleted!"})

# Get all hermannpupils

@app.route('/api/hermannkinder', methods=['GET'])
@token_required
def get_hermannpupils(current_user):
    all_hermannpupils = Hermannpupil.query.all()
    result = hermannpupils_schema.dump(all_hermannpupils)
    return jsonify(result)

# Get all hermannpupils of a class

@app.route('/api/hermannkinder/<group>', methods=['GET'])
@token_required
def get_grouphermannpupils(current_user, group):
    group_hermannpupils = Hermannpupil.query.filter_by(group = group).all()
    result = hermannpupils_schema.dump(group_hermannpupils)
    return jsonify(result)

# Get specific hermannpupil

@app.route('/api/hermannkind/<id>', methods=['GET'])
@token_required
def get_hermannpupil(current_user, id):
    this_hermannpupil = db.session.query(Hermannpupil).get(id)
    return hermannpupil_schema.jsonify(this_hermannpupil)

# Create a Schoolday

@app.route('/api/schultag', methods=['POST'])
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

# Get all schooldays

@app.route('/api/schultage', methods=['GET'])
@token_required
def get_schooldays(current_user):
    all_schooldays = db.session.query(Schoolday).all()
    result = schooldays_schema.dump(all_schooldays)
    return jsonify(result)

# Get specific schoolday

@app.route('/api/schultag/<date>', methods=['GET'])
@token_required
def get_schooday(current_user, date):
    stringtodatetime = datetime.strptime(date, '%Y-%m-%d').date()
    this_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    return schoolday_schema.jsonify(this_schoolday)

# Delete specific schoolday

@app.route('/api/schultag/<date>', methods=['DELETE'])
@token_required
def delete_schoolday(current_user, date):
    stringtodatetime = datetime.strptime(date, '%Y-%m-%d').date()
    this_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    db.session.delete(this_schoolday)
    db.session.commit()
    return jsonify( {"message": "The schoolday was deleted!"})


# Create a missedclass

@app.route('/api/fehlzeit', methods=['POST'])
@token_required
def add_missedclass(current_user):
    missedpupil_id = request.json['missedpupil_id']
    missedday = request.json['missedday']
    stringtodatetime = datetime.strptime(missedday, '%Y-%m-%d').date()
    this_schoolday = db.session.query(Schoolday).filter(Schoolday.schoolday == stringtodatetime ).first()
    missedday_id = this_schoolday.id
    missedclass_exists = db.session.query(MissedClass).filter(MissedClass.missedday_id == missedday_id, MissedClass.missedpupil_id == missedpupil_id ).first() is not None
    if missedclass_exists == True :
        return jsonify( {"message": "This missed class exists already - please update instead!"})
    else:    
        missedtype = request.json['missedtype']
        excused = request.json['excused']
        contacted = request.json['contacted']
        new_missedclass = MissedClass(missedpupil_id, missedday_id, missedtype, excused, contacted)
        db.session.add(new_missedclass)
        db.session.commit()
        return missedclass_schema.jsonify(new_missedclass)

# Get all missedclasses

@app.route('/api/fehlzeiten', methods=['GET'])
@token_required
def get_missedclasses(current_user):
    all_missedclasses = MissedClass.query.all()
    result = pupilmissedclasses_schema.dump(all_missedclasses)
    return jsonify(result)

# Get specific missedclass

@app.route('/api/fehlzeit/<id>', methods=['GET'])
@token_required
def get_missedclass(current_user, id):
    this_missedclass = db.session.query(MissedClass).get(id)
    return pupilmissedclass_schema.jsonify(this_missedclass)

# Update a missedclass

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

# Update a missedtype from a pupil on a certain day

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

# Update an excused bool from a pupil on a certain day

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

# Update a contacted bool from a pupil on a certain day

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

# Delete missedclass from a certain pupil on a certain day

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
   
# Delete a missedclass

@app.route('/api/fehlzeit/<id>', methods=['DELETE'])
@token_required
def delete_missedclass(current_user, id):
    missedclass = db.session.query(MissedClass).get(id)
    db.session.delete(missedclass)
    db.session.commit()
    return jsonify( {"message": "The missed class was deleted!"})

# Create an admonition

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

# Get all admonitions

@app.route('/api/karten', methods=['GET'])
@token_required
def get_admonitions(current_user):
    all_admonitions = Admonition.query.all()
    result = pupiladmonitions_schema.dump(all_admonitions)
    return jsonify(result)

# Get specific admonition

@app.route('/api/karte/<id>', methods=['GET'])
@token_required
def get_admonition(current_user, id):
    this_admonition = db.session.query(Admonition).get(id)
    return pupiladmonition_schema.jsonify(this_admonition)

# Update an admonition

@app.route('/api/karte/<id>', methods=['PATCH'])
@token_required
def update_admonition(current_user, id):
    admonition = Admonition.query.get(id)
    admonition.admonitiontype = request.json['admonitiontype']
    admonition.admonitionreason = request.json['admonitionreason']
    db.session.commit()
    return admonition_schema.jsonify(admonition)

# Delete an admonition

@app.route('/api/karte/<id>', methods=['DELETE'])
@token_required
def delete_admonition(current_user, id):
    admonition = db.session.query(Admonition).get(id)
    db.session.delete(admonition)
    db.session.commit()
    return jsonify( {"message": "The admonition was deleted!"})

# Delete an admonition from a certain pupil on a certain day

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


# Create a corona status

@app.route('/api/coronastatus', methods=['POST'])
@token_required
def add_coronastatus(current_user):
    coronapupil_id = request.json['coronapupil_id']
    untildate_string = request.json['untildate']
    corona_status = request.json['corona_status']
    untildate = datetime.strptime(untildate_string, '%Y-%m-%d').date()
    coronastatus_exists = db.session.query(CoronaStatus).filter(CoronaStatus.coronapupil_id == coronapupil_id ).first() is not None
    if coronastatus_exists == True :
        return jsonify( {"message": "This corona status exists already - please update instead!"})
    else:    

        new_coronastatus = CoronaStatus(coronapupil_id, corona_status, untildate)
        db.session.add(new_coronastatus)
        db.session.commit()
        return coronastatus_schema.jsonify(new_coronastatus)

# Update a corona status status

@app.route('/api/coronastatus/status/<id>', methods=['PATCH'])
@token_required
def update_coronastatus_status(current_user, id):
    this_coronastatus = db.session.query(CoronaStatus).filter(CoronaStatus.coronapupil_id == id ).first() 
    this_coronastatus.corona_status = request.json['corona_status']
    # untildate_string = request.json['untildate']
    # this_coronastatus.untildate = datetime.strptime(untildate_string, '%Y-%m-%d').date()
    
    db.session.commit()
    return coronastatus_schema.jsonify(this_coronastatus)

# Update a corona status untildate

@app.route('/api/coronastatus/date/<id>', methods=['PATCH'])
@token_required
def update_coronastatus_date(current_user, id):
    this_coronastatus = db.session.query(CoronaStatus).filter(CoronaStatus.coronapupil_id == id ).first() 
    # this_coronastatus.corona_status = request.json['corona_status']
    untildate_string = request.json['untildate']
    this_coronastatus.untildate = datetime.strptime(untildate_string, '%Y-%m-%d').date()
    
    db.session.commit()
    return coronastatus_schema.jsonify(this_coronastatus)

# Get all corona statuses

@app.route('/api/coronastatus', methods=['GET'])
@token_required
def get_coronastatuses(current_user):
    all_coronastatuses = CoronaStatus.query.all()
    result = coronastatuses_schema.dump(all_coronastatuses)
    return jsonify(result)

# Delete corona status from a certain pupil

@app.route('/api/coronastatus/<id>', methods=['DELETE'])
@token_required
def delete_coronastatus_with_id(current_user, id):
    this_coronastatus = db.session.query(CoronaStatus).filter(CoronaStatus.coronapupil_id == id).first() 

    db.session.delete(this_coronastatus)
    db.session.commit()
    return jsonify( {"message": "The corona status was deleted!"})

# Run server

if __name__ == '__main__':
    app.run(debug=True)
