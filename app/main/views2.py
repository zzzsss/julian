# Some of the most important pages (To show, write and send letters)
from flask import render_template, flash, request, redirect, url_for
from .. import db, matcher
from ..models import User, Letter, Letter_temp, Letter_system, add_commit_one, add_commit_ones, Log
from . import main
from .forms import *
from .helpers import *
from datetime import datetime

# To show a letter
@main.route('/letters/<int:lid>')
def letters(lid):
    """ To show one letter and some operations for this one
    :Description: Only when current-user is sender or receiver
    :param lid: the id of the letter
    :Use: User.get_one_byid; Letter.get_one_byid; Letter_temp.get_one_byid; get_info_reply
    """
    user = get_user_or_401()
    # get the letter corresponding to lid
    letter = get_one_byid(Letter, lid)
    # if current-user is not sender or receiver, then no chance
    if user.id not in [letter.send_id, letter.recv_id]:
        flash("You can not see this letter.")
        abort(401)
    # check for the letter
    info_reply, _ = get_info_reply(me=user, letter=letter)
    # check and change the status
    me_checked = None
    if user.id == letter.recv_id:
        if letter.status == Letter.MC_STA_ON:
            abort(401)
        elif letter.status == Letter.MC_STA_SENT:
            letter.status = Letter.MC_STA_OPN   #open it
            add_commit_one(letter)
    else:
        if letter.type == Letter.MC_TO_TMP:
            me_checked = get_one_byid(Letter_temp, letter.id).checked
    # todo: maybe rethink about the interface to the html
    return render_template("one_letter.html", letter=letter, info_reply=info_reply,
                           me=user, me_check=me_checked, datetime=datetime)

# To write a letter
@main.route('/writings', methods=['GET','POST'])
def writings():
    """ To create a letter
    :To-whom: depend on the args (checked by the order of): 1.system=1, 2.uid 3.lid
    :return:
    """
    user = get_user_or_401()
    # first check the args to get the receiver
    # 1.1 system
    if_system = request.args.get('system', None)
    if if_system is not None:
        form = LetterForm()
        if form.validate_on_submit():
            # post a to-system letter (three layers of letters)
            l0 = Letter(send_id=user.id, type=Letter.MC_TO_SYS, title=form.title.data, text=form.text.data)
            add_commit_one(l0)
            l1 = Letter_temp(id=l0.id)  # no sid now
            l2 = Letter_system(id=l0.id)
            add_commit_one(l1)
            add_commit_one(l2)
            return render_template('writings_ok.html')
        return render_template('writings.html', form=form, system=1, other=None, lo=None)
    # 1.2 uid
    num_uid = request.args.get('uid', None, int)
    num_lid = request.args.get('lid', None, int)
    if num_uid is not None:
        # first check if friend-ok
        other = get_one_byid(User, num_uid)
        f = Friend.get_one_bytwoid(user.id, num_uid)
        if other is None or f is None or f.status != Friend.MC_STA_OK:
            if num_lid is None:
                abort(401)
            # else: # fall through to num_lid check!! This and the link in writings.html guarantees
            #       # that if <friend-ok>, always send with uid arg
        else:
            form = LetterForm()
            if form.validate_on_submit():
                # post a normal letter
                l0 = Letter(send_id=user.id, recv_id=num_uid, type=Letter.MC_TO_FR,
                            title=form.title.data, text=form.text.data)
                add_commit_one(l0)
                return render_template('writings_ok.html')
            return render_template('writings.html', form=form, system=None, other=other, lo=None)
    # 1.3 lid -- if already friend, should use uid=?
    if num_lid is not None:
        # check, re-use the get_info_reply
        info_reply, those = get_info_reply(user, num_lid)
        if info_reply is None:
            abort(401)
        letter_origin = those[1]
        other = those[2]
        letter_temp_origin = those[4]
        # to see whether one has checked or not
        tmp_checked = checked_forone(user, letter_temp_origin.sid)
        if tmp_checked:
            form = LetterForm()
        else:
            form = LetterTempForm()     # with an additional check
        if form.validate_on_submit():
            # post a temp letter
            l0 = Letter(send_id=user.id, recv_id=other.id, type=Letter.MC_TO_TMP,
                        title=form.title.data, text=form.text.data)
            add_commit_one(l0)
            to_check = False    # whether this letter has check
            if not tmp_checked and form.checked.data:
                to_check = form.checked.data
            l1 = Letter_temp(id=l0.id, sid=letter_temp_origin.sid, checked=to_check)
            add_commit_one(l1)
            # change the replied field
            letter_temp_origin.replied = True
            add_commit_one(letter_temp_origin)
            return render_template('writings_ok.html')
        return render_template('writings.html', form=form, system=None, other=other,
                               lo=letter_origin, checked=tmp_checked)
    # 1.4 no-one
    return render_template('writings2whom.html')

# To send the letters
# the magic, which changes the letters and generate the sessions
@main.route('/magic')
def magic():
    """ To send the letters, deal with three kinds of letters
        --- and also report some logs.
        <!!> This function is quite tedious and bad-written <!!>
    """
    # print("Magic start!!")
    # in fact need authorization, but leave it for simplicity #todo
    # step 1: send the letters to friends
    letters = Letter.query.filter(Letter.status == Letter.MC_STA_ON).filter(Letter.type == Letter.MC_TO_FR).all()
    num_s1 = len(letters)
    for l in letters:
        l.status = Letter.MC_STA_SENT
        l.sent_time = datetime.utcnow()
        f = Friend.get_one_bytwoid(l.send_id, l.recv_id)
        f.num += 1
        add_commit_one(f)
    add_commit_ones(letters)
    # step 2: send the temp letters and possibly add friends
    letters2 = db.session.query(Letter, Letter_temp).filter(Letter.id == Letter_temp.id)\
            .filter(Letter.status == Letter.MC_STA_ON).filter(Letter.type == Letter.MC_TO_TMP).all()
    num_s2 = len(letters2)
    num_newf = 0    # new friendship
    for l, lt in letters2:
        l.status = Letter.MC_STA_SENT
        l.sent_time = datetime.utcnow()
        s = lt.session
        f = Friend.get_one_bytwoid(s.uid1, s.uid2)
        s.num += 1
        s.last_time = datetime.utcnow()
        f.num += 1
        if s.status == Session.MC_STA_OPEN:
            # check for the check
            if lt.checked:
                if l.send_id == s.uid1:
                    s.u1_checked = True
                else:
                    s.u2_checked = True
                # add friend if not
                if s.u1_checked and s.u2_checked:
                    s.status = Session.MC_STA_SUCC
                    f.status = Friend.MC_STA_OK
                    num_newf += 1
        add_commit_ones([l, s, f])
    # step 3: match system letters and create sessions
    letters3 = Letter_system.query.filter(Letter_system.matched==False).all()
    letters_tomatch = [(l.letter_temp.letter, l.letter_temp, l) for l in letters3]
    pairs = matcher.match(letters_tomatch)  # return pairs of matches, no repeat
    # todo: add counts of unmatched times
    num_s3 = len(pairs)
    for a, b in pairs:
        if a[0].send_id > b[0].send_id:
            a, b = b, a
        # create session
        u1, u2 = a[0].send_id, b[0].send_id
        s = Session(uid1=u1, uid2=u2, num=2, last_time=datetime.utcnow())
        add_commit_one(s)
        # possibly create (temp) friend
        f = Friend.get_one_bytwoid(u1, u2)
        if f is None:
            f = Friend(uid1=u1, uid2=u2, sid=s.id, num=2)
            add_commit_one(f)
        # change the states for letters
        a[0].recv_id = u2
        b[0].recv_id = u1
        a[0].status = Letter.MC_STA_SENT
        b[0].status = Letter.MC_STA_SENT
        a[0].sent_time = datetime.utcnow()
        b[0].sent_time = datetime.utcnow()
        a[1].sid = s.id
        b[1].sid = s.id
        a[2].matched = True
        b[2].matched = True
        add_commit_ones(list(a)+list(b))
    # step 4: add a log for the system logging
    num_sent = num_s1 + num_s2 + num_s3*2
    num_news = num_s3
    num_newf = num_newf
    num_users = User.query.count()
    num_letters = Letter.query.count()
    num_letters_sys = Letter_system.query.count()
    num_sessions = Session.query.count()
    num_friends = Friend.query.count()
    log = Log(num_sent=num_sent, num_news=num_news, num_newf=num_newf, num_users=num_users, num_letters=num_letters,
              num_letters_sys=num_letters_sys, num_sessions=num_sessions, num_friends=num_friends)
    add_commit_one(log)
    return redirect(url_for("main.logs"))

@main.route('/logs')
def logs():
    ls = Log.query.filter().all()
    # print(len(ls))
    return render_template("logs.html", logs=ls, datetime=datetime)
