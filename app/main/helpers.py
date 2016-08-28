from flask import session, abort
from ..models import get_one_byid, User, Letter, Friend, Letter_temp, Session


def get_user_or_401():
    """ To assert login and return current user or abort 401
    :return: an object of User
    :Used-by: almost all the views (excluding login and register)
    """
    if not session.get('logged_in'):
        abort(401)
    self_uid = session['uid']
    user = get_one_byid(User, self_uid)
    return user

# arguments of /receivings
Arg_receivings_name = "filter"
Arg_receivings_list = ["all", "unread", "read", "frompenpals", "fromtemp"]
Arg_receivings_f = {
    "all": lambda x: x,
    "unread": lambda x: x.filter(Letter.status != Letter.MC_STA_OPN),
    "read": lambda x: x.filter(Letter.status == Letter.MC_STA_OPN),
    "frompenpals": lambda x: x.filter(Letter.type == Letter.MC_TO_FR),
    "fromtemp": lambda x: x.filter(Letter.type == Letter.MC_TO_FR)
}

# arguments of /sendings
Arg_sendings_name = "filter"
Arg_sendings_list = ["all", "unsent", "sent", "topenpals", "totemp"]
Arg_sendings_f = {
    "all": lambda x: x,
    "unsent": lambda x: x.filter(Letter.status == Letter.MC_STA_ON),
    "sent": lambda x: x.filter(Letter.status != Letter.MC_STA_ON),
    "topenpals": lambda x: x.filter(Letter.type == Letter.MC_TO_FR),
    "totemp": lambda x: x.filter(Letter.type == Letter.MC_TO_FR)
}

# arguements of /writings
Arg_writings_names = ["system", "uid", "lid"]

# checkers
# -- can_see: display info if who-can-see is ALL or FRIEND
# -- can_write: has link for writing if friend-OK
# -- get_info_reply: could reply a letter
def can_see(me, other, f):
    """ To get whether me can see other's profile
    :param: me and other could be uid or User instance, f could be Friend instance or None
    :return: (bool, (me, other, f))
    :Use: User.get_one_byid, Friend.get_one_bytwoid
    :Used-by: .penpals/<uid>
    :return: if_can_see(boolean), (me, other, f)
    """
    # get Users
    if not isinstance(me, User):
        me = get_one_byid(User, me)
    if not isinstance(other, User):
        other = get_one_byid(User, other)
    # get Friend info
    if f is None:
        f = Friend.get_one_bytwoid(me.id, other.id)
    # return the judgements
    if f is None:
        return False, (me, other, f)
    if_see = (other.who_can_see == User.MC_WHO_ALL) \
        or (other.who_can_see == User.MC_WHO_FR and f.status == Friend.MC_STA_OK)
    return if_see, (me, other, f)

def can_write(me, other, f):
    """ To get whether me can write to other
    :Description: same as "can_see"
    """
    # todo: a little repeated, may be improved
    # get Users
    if not isinstance(me, User):
        me = get_one_byid(User, me)
    if not isinstance(other, User):
        other = get_one_byid(User, other)
    # get Friend info
    if f is None:
        f = Friend.get_one_bytwoid(me.id, other.id)
    # return the judgements
    if f is None:
        return False, (me, other, f)
    if_write = (f.status == Friend.MC_STA_OK)
    return if_write, (me, other, f)

def get_info_reply(me, letter):
    """ To get the information for whether a reply could be ok
            --- this may be somewhat complicated and not so clear
    :param-need: At least the first two are needed, me and letter
    :return: None or {uid:...,lid:...}, (...)
    :Used-by: .letters/<lid>
    """
    # at least get user and letter
    if not isinstance(me, User):
        me = get_one_byid(User, me)
    if not isinstance(letter, Letter):
        letter = get_one_byid(Letter, letter)
    # 1. if not receiver, return None
    if not letter.receiver or letter.receiver.id != me.id:
        return None, (me, letter)
    # 2. check further
    else:
        other = letter.receiver
        f = Friend.get_one_bytwoid(me.id, other.id)
        # 2.0. if no friendship
        if f is None:
            return None, (me, letter)
        # 2.1. if friend-ok
        if f.status == Friend.MC_STA_OK:
            return {'uid': other.id, 'lid': letter.lid}, (me, letter, other, f)
        # 2.2. if friend-temp, each temp-letter can be replied only once
        # todo: adding time limit for the temp-letters
        letter_temp = get_one_byid(Letter_temp, letter.id)
        if letter_temp.replied:
            return None, (me, letter, other, f, letter_temp)
        else:
            return {'uid': None, 'lid': letter.lid, 'checked_for_temp': letter_temp.checked}, \
                   (me, letter, other, f, letter_temp)

def checked_forone(me, s):
    """ To see whether one has checked to request for penpals or not in a session
    :Used-by: .writings
    """
    if not isinstance(me, User):
        me = get_one_byid(User, me)
    if not isinstance(s, Session):
        s = get_one_byid(Session, s)
    if me.id == s.uid1:
        return s.u1_checked
    elif me.id == s.uid2:
        return s.u2_checkd
    else:
        abort(500)
