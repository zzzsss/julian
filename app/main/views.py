from flask import render_template, session, redirect, url_for, request, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from .. import db
from . import main
from .forms import *
from .helpers import *
from ..models import Letter_temp, Session, Friend
from datetime import datetime

HOMEPAGE = ".welcome"

# ========== 0. for managers ========== #
@main.route('/newworld')
def newworld():
    # create the database
    db.create_all()
    return "New world has been created."

# ========== 1. login and register ========== #
@main.route('/', methods=['GET', 'POST'])
@main.route('/login', methods=['GET', 'POST'])
def login():
    """ To login
    :Description: <Post> get a user and check password
    :Use: LoginForm; User.get_one_byname
    """
    if session.get('logged_in'):
        return redirect(url_for(HOMEPAGE))   # jump to default home page
    error = None
    form = LoginForm()
    if form.validate_on_submit():   # if post and the form is valid
        username = form.name.data
        password = form.passwd.data
        user = User.get_one_byname(username)
        if user is None:
            error = 'Invalid username'
        elif not check_password_hash(user.password_hash, password):
            error = 'invalid password'
        else:   # ok for login
            session['logged_in'] = True
            session['username'] = user.username
            session['uid'] = user.id
            flash('You were logged in.')
            return redirect(url_for(HOMEPAGE))
    return render_template('login.html', form=form, error=error)

@main.route('/logout')
def logout():
    """ To log out
    :Description: quick and easy, almost nothing to do
    :Use:
    """
    if session.pop('logged_in', None):
        flash('You were logged out.')
    return redirect('/')

@main.route('/register', methods=['GET','POST'])
def register():
    """ To register a new user
    :Description: two conditions(fresh-new username, identical passwords)
    :Use: RegisterForm; User.get_one_byname; User.add_one
    """
    error = None
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.name.data
        password = form.passwd.data
        password2 = form.passwd2.data
        user = User.get_one_byname(username)
        if user is not None:
            error = "The username is already taken"
        elif password != password2:
            error = "The two passwords do not match"
        else:
            User.add_one(username, generate_password_hash(password), form.penname.data)
            flash('You were successfully registered and can login now')
            return redirect(url_for('.login'))
    return render_template('register.html', form=form, error=error)

# ========= 2. users =============== #
# Notice these all needs login first (check session)
@main.route('/welcome')
def welcome():
    """ Like the homepage
    :Description:
    :Use: User.get_one_byid
    """
    user = get_user_or_401()
    return render_template('welcome.html', user=user)

@main.route('/settings', methods=['GET', 'POST'])
def settings():
    """ To set the settings for a user
    :Description:
    :Use: InfoForm; User.get_one_byid; User.assign_*form
    """
    user = get_user_or_401()
    form = InfoForm()
    if form.validate_on_submit():
        # print(user)
        user.assign_fromform(form)      # could have use Form.populate_obj, but for safety
        flash("Changes saved.")
        return redirect(url_for('.settings'))
    else:
        user.assign_toform(form)
        return render_template('settings.html', user=user, form=form)

@main.route('/receivings')
def receivings():
    """ To list the received letters for this user
    :Description: With a parameter for filters (helpers.Arg_receivings) [/receivings?filter=*]
                --- only the letters sent could been seen
    :Use: User.get_one_byid; Letter(direct query)
    """
    user = get_user_or_401()
    # get the display parameters, 'all' by default
    param = request.args.get(Arg_receivings_name, Arg_receivings_list[0])
    if param not in Arg_receivings_f:
        param = Arg_receivings_list[0]
    # Here, directly use query (no wrapper for simplicity): can only see the letters sent
    letters_toquery = Letter.query.filter(Letter.recv_id == user.id).filter(Letter.status != Letter.MC_STA_ON)
    letters = Arg_receivings_f[param](letters_toquery).order_by(Letter.write_time).all()
    # finally render
    return render_template('receivings.html', letters=letters, l=Arg_receivings_list, datetime=datetime)

@main.route('/sendings')
def sendings():
    """ To list the sent letters for this user
    :Description: With a parameter for filters (helpers.Arg_sendings) [/sendings?filter=*]
    :Use: User.get_one_byid; Letter(direct query)
    """
    user = get_user_or_401()
    # get the display parameters, 'all' by default
    param = request.args.get(Arg_sendings_name, Arg_sendings_list[0])
    if param not in Arg_sendings_f:
        param = Arg_sendings_list[0]
    # Here, directly use query (no wrapper for simplicity)
    letters_toquery = Letter.query.filter(Letter.send_id == user.id)
    letters = Arg_sendings_f[param](letters_toquery).order_by(Letter.write_time).all()
    # finally render
    return render_template('sendings.html', letters=letters, l=Arg_sendings_list, datetime=datetime)

@main.route('/sessions')
def sessions0():
    """ To show the sessions (one for each letter-match)
    :Use: User.get_one_byid; Session.get_byuid
    """
    user = get_user_or_401()
    # get the user's sessions
    sessions = Session.get_byuid(user.id)
    # get the user info of the other ones
    others = []
    for s in sessions:
        if s.user1 == user:
            others.append(s.user2)
        else:
            others.append(s.user1)
    return render_template('sessions.html', sessions=sessions, others=others, zip=zip)

@main.route('/sessions/<int:sid>')
def sessions(sid):
    """ To display the letters of one session
    :Description: Have to be one of the users
    :Use: User.get_one_byid; Session.get_one_byid; Letter_temp.get_bysid_joint
    """
    user = get_user_or_401()
    # get the session
    s = get_one_byid(Session, sid)
    # have to be one of users, otherwise unauthorized
    other = None
    if user.id == s.user1.id:
        other = s.user2
        checked_me, checked_other = s.u1_checked, s.u2_checked
    elif user.id == s.user2.id:
        other = s. user1
        checked_me, checked_other = s.u2_checked, s.u1_checked
    else:
        flash("You can not see this session.")
        checked_me, checked_other = None, None
        abort(401)
    # get all the letters
    letters = Letter_temp.get_bysid_joint(s.id)
    # ---------- Fix Bug for v0.1.1: can not display unsent in-box letters ---------- #
    letters = [x for x in letters if not (user.id==x[0].recv_id and x[0].status==Letter.MC_STA_ON)]
    # ---------- Fix Bug for v0.1.1 ---------- #
    return render_template('one_session.html', letters=letters, checked=[checked_me, checked_other],
                           other=other, s=s, datetime=datetime)

@main.route('/penpals')
def penpals0():
    """ To display all the penpals.
    :Use: User.get_one_byid; Friend.get_byuid
    """
    user = get_user_or_401()
    fs = Friend.get_byuid(user.id)
    fs = [f for f in fs if f.status == Friend.MC_STA_OK]    # only ok friends
    fus = []     # add the User info of friends: list of (Friend, User)
    for f in fs:
        if user.id == f.user1.id:
            fus.append((f, f.user2))
        elif user.id == f.user2.id:
            fus.append((f, f.user1))
        else:
            abort(500)
    # sort by penname
    fus.sort(key=lambda x: x[1].penname)
    return render_template('penpals.html', fus=fus)

@main.route('/penpals/<int:uid>')
def penpals(uid):
    """ To see the info of a user.
    :Description: is a penpal if f.status==ok, otherwise only temp ones
    :Use: User.get_one_byid; Friend.get_one_bytwoid
    """
    user = get_user_or_401()
    # if it is self, jump to the settings
    if uid == user.id:
        return redirect(url_for(".settings"))
    # get the friendship
    f = Friend.get_one_bytwoid(user.id, uid)
    if f is None:
        flash("You can not see this user.")
        abort(401)
    # get the other one
    if user.id == f.user1.id:
        other = f.user2
    else:
        other = f.user1
    # check for the status
    if_display, _ = can_see(user, other, f)
    if_write, _ = can_write(user, other, f)
    return render_template('one_penpal.html', f=f, other=other, if_display=if_display, if_write=if_write)
