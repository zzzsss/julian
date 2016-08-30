import unittest
from flask import current_app, url_for, session
# from ..app import create_app
# from ..app.models import User, Letter, Friend
from app import create_app, db
from app.models import User, Letter, Friend
from random import random, randint

import logging
l2 = logging.getLogger('test')
l2.setLevel(logging.INFO)
hdr = logging.StreamHandler()
formatter = logging.Formatter('L2: [%(asctime)s] %(name)s:%(levelname)s: %(message)s')
hdr.setFormatter(formatter)
l2.addHandler(hdr)

def bychance(c=0.5):
    return random() < c

CHANCE_TMP_CHECK=0.6
CHANCE_REPLY_TMP=0.6
CHANCE_WRITE2_FR=0.6

# For testing with medium scale
#   -- 23 users each with 2 rounds of matches
class MediumTestCase(unittest.TestCase):
    def setUp(self):
        self._lnum = 0
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        db.drop_all()
        # set slqalchemy's logger
        if True:
            l = logging.getLogger('sqlalchemy.engine')
            l.setLevel(logging.INFO)
            hdr = logging.StreamHandler()
            formatter = logging.Formatter('[%(asctime)s] %(name)s:%(levelname)s: %(message)s')
            hdr.setFormatter(formatter)
            l.addHandler(hdr)
        # start
        l2.info("START")
        db.create_all()     # clear them at setup
        self.client = self.app.test_client(use_cookies=True)

    @property
    def lnum(self):
        self._lnum += 1
        return self._lnum-1

    def tearDown(self):
        db.session.remove()
        # db.drop_all()
        self.app_context.pop()

    # helpers
    # conventions: username/penname/passwd are all the same
    def h_login(self, name):
        l2.info("Login for %s" % name)
        r = self.client.post(url_for('main.login'), data={'name':name, 'passwd':name})

    def h_logout(self):
        # l2.info("Logout for %s" % session['username'])
        l2.info("Logout")
        r = self.client.get(url_for('main.logout'))

    def h_register(self, name):
        l2.info("Register for %s" % name)
        r = self.client.post(url_for('main.register'),
                             data={'name':name, 'penname':name, 'passwd':name, 'passwd2':name})

    def h_settings(self, name, l=False):
        self.h_login(name) if l else None
        l2.info("Settings for %s" % name)
        r = self.client.post(url_for('main.settings'),
                data={'penname':name, 'age': randint(18, 30), 'gender':(0 if bychance() else 1),
                    'self_intro':"This is %s"%name, "who_can_see": randint(0, 2), "matching_gender": randint(0, 2)})
        self.h_logout() if l else None

    def h_magic(self):
        l2.info("Magic: -----------")
        r = self.client.get(url_for("main.magic"))
        # print(r.data)

    def h_writings_sys(self, name, l=False):
        self.h_login(name) if l else None
        l2.info("Writings for %s to system" % name)
        tt = "From %s sys-letter %s"%(name, self.lnum)
        r = self.client.post(url_for('main.writings', system=1), data={'title': tt, 'text':"Text:"+tt})
        self.h_logout() if l else None

    def h_writings_fr(self, name, fid, l=False):
        self.h_login(name) if l else None
        l2.info("Writings for %s to uid=%s" % (name, fid))
        tt = "From %s friend-letter %s"%(name, self.lnum)
        r = self.client.post(url_for('main.writings', uid=fid), data={'title': tt, 'text':"Text:"+tt})
        self.h_logout() if l else None

    def h_writings_tmp(self, name, lid, l=False):
        self.h_login(name) if l else None
        l2.info("Writings for %s to lid=%s" % (name, lid))
        tt = "From %s temp-letter %s"%(name, self.lnum)
        r = self.client.post(url_for('main.writings', lid=lid),
                    data={'title': tt, 'text':"Text:"+tt, 'checked':True if bychance(CHANCE_TMP_CHECK) else False})
        self.h_logout() if l else None

    def h_get_tmp(self, name):
        # get the ids of received tmp letters, search db
        me = User.get_one_byname(name)
        those = Letter.query.filter(Letter.recv_id==me.id).filter(Letter.status!=Letter.MC_STA_ON)\
            .filter(Letter.type!=Letter.MC_TO_FR).all()
        return [x.id for x in those]

    def h_get_fr(self, name):
        # get the ids of ok-friends, search db
        me = User.get_one_byname(name)
        those = Friend.get_byuid(me.id)
        return [x.uid1+x.uid2-me.id for x in those]

    # test
    def test_it(self):
        # this is actually a whole-scale testing
        # step 1: register them and settings
        them = "abcdefghijklmnopqrstuvw"[:]
        for i in them:
            self.h_register(i)
            self.h_settings(i, True)
        # step 2: each write a system letter and magic1
        for i in them:
            self.h_writings_sys(i, True)
        self.h_magic()
        # step 3: each write another system letter, reponse temp and magic2
        for i in them:
            self.h_login(i)
            self.h_writings_sys(i)
            lids = self.h_get_tmp(i)
            for one in lids:
                if bychance(CHANCE_REPLY_TMP):
                    self.h_writings_tmp(i, one)
            self.h_logout()
        self.h_magic()
        # step 4: response temp, write to friend and magics
        for time in range(2):
            for i in them:
                self.h_login(i)
                lids = self.h_get_tmp(i)
                for one in lids:
                    if bychance(CHANCE_REPLY_TMP):
                        self.h_writings_tmp(i, one)
                fids = self.h_get_fr(i)
                for one in fids:
                    if bychance(CHANCE_WRITE2_FR):
                        self.h_writings_fr(i, one)
                self.h_logout()
            self.h_magic()
        return
