#!/usr/bin/env python
import os
from app import create_app, db
from app.models import Log, User, Letter, Letter_temp, Letter_system, Session, Friend

from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
    return dict(app=app, db=db, Log=Log, User=User, Letter=Letter, Letter_temp=Letter_temp,
                Letter_system=Letter_system, Session=Session, Friend=Friend)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

if __name__ == '__main__':
    manager.run()

# todo-list:
# flask-login, system-manage, dealing-errors

# FIX: v0.1.1
# 2 fixed: one-session-filter, get_info_reply.check-fr
# unfixed: one-letter display, /writings/lid=? to already-friend, release checked from letter
