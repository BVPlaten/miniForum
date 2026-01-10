from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    """Login form with username and password"""
    username = StringField('Benutzername', validators=[
        DataRequired(message='Benutzername ist erforderlich'),
        Length(min=3, max=80, message='Benutzername muss zwischen 3 und 80 Zeichen lang sein')
    ])
    password = PasswordField('Passwort', validators=[
        DataRequired(message='Passwort ist erforderlich')
    ])
    remember_me = BooleanField('Angemeldet bleiben')
    submit = SubmitField('Anmelden')

class RegistrationForm(FlaskForm):
    """User registration form"""
    username = StringField('Benutzername', validators=[
        DataRequired(message='Benutzername ist erforderlich'),
        Length(min=3, max=80, message='Benutzername muss zwischen 3 und 80 Zeichen lang sein')
    ])
    email = StringField('E-Mail', validators=[
        DataRequired(message='E-Mail ist erforderlich'),
        Email(message='Ungültige E-Mail-Adresse'),
        Length(max=120, message='E-Mail darf maximal 120 Zeichen lang sein')
    ])
    password = PasswordField('Passwort', validators=[
        DataRequired(message='Passwort ist erforderlich'),
        Length(min=6, message='Passwort muss mindestens 6 Zeichen lang sein')
    ])
    password2 = PasswordField('Passwort wiederholen', validators=[
        DataRequired(message='Bitte Passwort wiederholen'),
        EqualTo('password', message='Passwörter müssen übereinstimmen')
    ])
    submit = SubmitField('Registrieren')

    def validate_username(self, username):
        """Validate username uniqueness"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Benutzername bereits vergeben')

    def validate_email(self, email):
        """Validate email uniqueness"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('E-Mail-Adresse bereits registriert')

class ResetPasswordRequestForm(FlaskForm):
    """Password reset request form"""
    email = StringField('E-Mail', validators=[
        DataRequired(message='E-Mail ist erforderlich'),
        Email(message='Ungültige E-Mail-Adresse')
    ])
    submit = SubmitField('Passwort zurücksetzen')

class ResetPasswordForm(FlaskForm):
    """Password reset form"""
    password = PasswordField('Neues Passwort', validators=[
        DataRequired(message='Passwort ist erforderlich'),
        Length(min=6, message='Passwort muss mindestens 6 Zeichen lang sein')
    ])
    password2 = PasswordField('Passwort wiederholen', validators=[
        DataRequired(message='Bitte Passwort wiederholen'),
        EqualTo('password', message='Passwörter müssen übereinstimmen')
    ])
    submit = SubmitField('Passwort ändern')