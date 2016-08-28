from flask_wtf import Form
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, \
    IntegerField, RadioField, SelectField, BooleanField
from wtforms.validators import DataRequired, NumberRange, Length, Email, Regexp
from wtforms import ValidationError

class LoginForm(Form):
    name = StringField('username:', validators=[DataRequired()])
    passwd = PasswordField('password:', validators=[DataRequired()])
    submit = SubmitField('Submit')

class RegisterForm(Form):
    name = StringField('username:', validators=[DataRequired()])
    passwd = PasswordField('password:', validators=[DataRequired()])
    passwd2 = PasswordField('password again:', validators=[DataRequired()])
    submit = SubmitField('Submit')

class InfoForm(Form):
    penname = StringField('penname:', validators=[DataRequired()])
    age = IntegerField('age:', validators=[NumberRange(0, 200)])
    gender = SelectField(label='gender:', choices=[(0, 'boy'), (1, 'girl'), (2, 'secret')], coerce=int)
    self_intro = TextAreaField('about me:')
    who_can_see = SelectField(label='who_can_see:', choices=[(0, 'all'), (1, 'penpals'), (2, 'nope')], coerce=int)
    matching_gender = SelectField(label='matching_gender:', choices=[(0, 'same'), (1, 'diff'), (2, 'whatever')], coerce=int)
    submit = SubmitField('Submit')

class LetterForm(Form):
    title = StringField('Title:', validators=[DataRequired()])
    text = TextAreaField('Text:')
    submit = SubmitField('Submit')

class LetterTempForm(Form):
    title = StringField('Title:', validators=[DataRequired()])
    text = TextAreaField('Text:')
    checked = BooleanField("Want to add penpal?")
    submit = SubmitField('Submit')
