from datetime import datetime
from . import db
# from .main.forms import InfoForm
# from flask_wtf import Form
from flask import abort
from sqlalchemy import or_, and_

# common helpers
def get_one_byid(d, i):
    """ To get the one (for all tables) by uid, should be always one if everything works ok
            --- otherwise 500 error
    """
    u = d.query.filter_by(id=i).all()
    if len(u) != 1:
        abort(500)
    return u[0]

def add_commit_one(one):
    """ To add and commit to a db
    """
    db.session.add(one)
    db.session.commit()

def add_commit_ones(ones):
    """ To add and commit to a db
    """
    db.session.add_all(ones)
    db.session.commit()

# ------------------- 0. System Log ------------------- #
class Log(db.Model):
    """ Some system information
    """
    __tablenames__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime(), default=datetime.utcnow)
    num_sent = db.Column(db.Integer)
    num_news = db.Column(db.Integer)
    num_newf = db.Column(db.Integer)
    num_users = db.Column(db.Integer)
    num_letters = db.Column(db.Integer)
    num_letters_sys = db.Column(db.Integer)
    num_sessions = db.Column(db.Integer)
    num_friends = db.Column(db.Integer)

# ------------------- 1. User ------------------- #
class User(db.Model):
    """ The User table, the information center for the users
    :Columns: identifications, info, preferences
    """
    __tablename__ = 'users'

    # some magic constants
    MC_GENDER_BOY, MC_GENDER_GIRL = 0, 1
    MC_WHO_ALL, MC_WHO_FR, MC_ALL_NON = 0, 1, 2
    MC_MATCH_SAME, MC_MATCH_OTHER, MC_MATCH_NON = 0, 1, 2

    # columns
    # columns-identification
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    # columns-info
    penname = db.Column(db.String(64))
    gender = db.Column(db.Integer, default=0)  # 0:boy, 1:girl
    # --- START who-can-see-this-fileds
    age = db.Column(db.Integer, default=0)
    self_intro = db.Column(db.Text(), default="")
    # --- END who-can-see-this-fileds
    # columns-preferences
    who_can_see = db.Column(db.Integer, default=1)  # 0:all, 1:pen-pals, 2.no-one
    matching_gender = db.Column(db.Integer, default=1)  # 0:same, 1:other, 2:not-care

    def __repr__(self):
        return '<User %s>' % self.__dict__

    # helper functions
    @staticmethod
    def get_one_byname(uname):
        """ To get the one user by username, should be one or None
        :Used-by: .login; .register
        """
        return User.query.filter_by(username=uname).first()

    @staticmethod
    def add_one(uname, pw_hash, penname="Anonymous"):
        """ To add a new user with username and hashed-pass
        :Used-by: .register
        """
        one = User(username=uname, penname=penname, password_hash=pw_hash)
        add_commit_one(one)

    # from and to the form, object methods
    def assign_toform(self, f):
        """ To fill into the InfoForm
        :Used-by: .settings(GET)
        """
        # assert isinstance(f, InfoForm)
        f.penname.data = self.penname
        f.age.data = self.age
        f.gender.data = self.gender
        f.self_intro.data = self.self_intro
        f.who_can_see.data = self.who_can_see
        f.matching_gender.data = self.matching_gender

    def assign_fromform(self, f):
        """ To change the data from InfoForm (may throw, maybe need further considerations)
        :Used-by: .settings(POST)
        """
        # assert isinstance(f, InfoForm)
        self.age = f.age.data
        self.penname = f.penname.data
        self.gender = f.gender.data
        self.self_intro = f.self_intro.data
        self.who_can_see = f.who_can_see.data
        self.matching_gender = f.matching_gender.data
        # print(self)
        add_commit_one(self)

# ------------------- 2. Letter ------------------- #
class Letter(db.Model):
    """ The letter table, model one letter
    :Used-by: .receivings and .sendings for listing the corresponding letters (direct query)
    """
    __tablename__ = 'letters'

    # some magic constants
    MC_TO_FR, MC_TO_SYS, MC_TO_TMP = 0, 1, 2
    MC_STA_ON, MC_STA_SENT, MC_STA_OPN = 0, 1, 2
    NOTE_TYPE = ["friend", "system", "temp"]
    NOTE_STATUS_SEND = ["unsent", "sent", "sent"]     # from sender's point of view
    NOTE_STATUS_RECV = ["unsent", "sent", "opened"]   # from receiver's point of view

    # columns
    id = db.Column(db.Integer, primary_key=True)
    send_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    recv_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    type = db.Column(db.Integer)    # 0:pen-pals, 1:system, 2:temp
    status = db.Column(db.Integer, default=0)  # 0:on-the-way, 1:sent, 2:opened
    write_time = db.Column(db.DateTime(), default=datetime.utcnow)
    sent_time = db.Column(db.DateTime())
    title = db.Column(db.Text())
    text = db.Column(db.Text())

    # relationships
    sender = db.relationship('User', foreign_keys=send_id)
    receiver = db.relationship('User', foreign_keys=recv_id)

class Letter_temp(db.Model):
    """ Temp letters, letters in this table must have a related session unless unmatched
    """
    __tablename__ = 'letters_temp'

    # columns
    id = db.Column(db.Integer, db.ForeignKey('letters.id'), primary_key=True)
    sid = db.Column(db.Integer, db.ForeignKey('sessions.id'), index=True)
    replied = db.Column(db.Boolean(), default=False)
    checked = db.Column(db.Boolean(), default=False)

    # relationships
    letter = db.relationship('Letter', foreign_keys=id)
    session = db.relationship('Session', foreign_keys=sid)

    @staticmethod
    def get_bysid_joint(sid):
        """ To get the letters for one session
        :return: a list of (letter, letter_temp)
        :Used-by: .sessions/<sid>
        """
        return db.session.query(Letter, Letter_temp).filter(Letter.id == Letter_temp.id)\
            .filter(Letter_temp.sid == sid).order_by(Letter.write_time).all()

class Letter_system(db.Model):
    __tablename__ = 'letters_system'

    # columns
    id = db.Column(db.Integer, db.ForeignKey('letters_temp.id'), primary_key=True)
    matched = db.Column(db.Boolean(), default=False)    # equal to Letter.status==on-the-way

    letter_temp = db.relationship('Letter_temp', foreign_keys=id)

# ------------------- 3. Session ------------------- #
class Session(db.Model):
    """ The session table, used to manage the letter-matches
    """
    __tablename__ = 'sessions'

    # some magic constants
    MC_STA_OPEN, MC_STA_NOPE, MC_STA_SUCC = 0, 1, 2

    # columns
    # uid1 < uid2
    id = db.Column(db.Integer, primary_key=True)
    uid1 = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    uid2 = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    num = db.Column(db.Integer, default=0)  # keep counts for convenience
    u1_checked = db.Column(db.Boolean(), default=False)
    u2_checked = db.Column(db.Boolean(), default=False)
    status = db.Column(db.Integer, default=0)  # 0:open, 1:nope, 2:success
    last_time = db.Column(db.DateTime(), default=datetime.utcnow)

    # relationships
    user1 = db.relationship('User', foreign_keys=uid1)
    user2 = db.relationship('User', foreign_keys=uid2)

    @staticmethod
    def get_byuid(uid):
        """ To get the sessions for one user
        :Used-by: .sessions
        """
        return Session.query.filter(or_(Session.uid1==uid, Session.uid2==uid)).order_by(Session.last_time).all()

# ------------------- 4. Friend ------------------- #
class Friend(db.Model):
    """ The table for maintaining friendships, notice that temp ones could also be friends
        --- temp ones are noted as temp, added for convenience of checking
    """
    # todo: currently assume a friendship can only have one session
    __tablename__ = 'friends'

    # some magic constants
    MC_STA_TEMP, MC_STA_OK = 0, 1

    # columns
    # uid1 < uid2
    id = db.Column(db.Integer, primary_key=True)
    uid1 = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    uid2 = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    sid = db.Column(db.Integer, db.ForeignKey('sessions.id'), index=True)   # the starting session
    status = db.Column(db.Integer, default=0)  # 0:temp(maybe non-friend) 1:ok,normal
    num = db.Column(db.Integer, default=0)  # keep counts for convenience

    # relationships
    user1 = db.relationship('User', foreign_keys=uid1)
    user2 = db.relationship('User', foreign_keys=uid2)
    session = db.relationship('Session', foreign_keys=sid)

    @staticmethod
    def get_byuid(uid):
        """ To get the friends for one user
        :Used-by: .penpals
        """
        return Friend.query.filter(or_(Friend.uid1==uid, Friend.uid2==uid)).all()

    @staticmethod
    def get_one_bytwoid(u1, u2):
        """ To get the one with two user id, return None if not found, abort(500) if more than one
        :Used-by: .penpals/<uid>
        """
        x = Friend.query.filter(or_(and_(Friend.uid1==u1, Friend.uid2==u2),
                                    and_(Friend.uid1==u2, Friend.uid2==u1))).all()
        if len(x) == 0:
            return None
        elif len(x) > 1:
            abort(500)
        return x[0]

