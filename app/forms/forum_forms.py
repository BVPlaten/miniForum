from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from app.models import Category

class ThreadForm(FlaskForm):
    """Form for creating new threads"""
    title = StringField('Titel', validators=[
        DataRequired(message='Titel ist erforderlich'),
        Length(min=5, max=200, message='Titel muss zwischen 5 und 200 Zeichen lang sein')
    ])
    content = TextAreaField('Inhalt', validators=[
        DataRequired(message='Inhalt ist erforderlich'),
        Length(min=10, message='Inhalt muss mindestens 10 Zeichen lang sein')
    ])
    submit = SubmitField('Thread erstellen')

class PostForm(FlaskForm):
    """Form for creating posts and replies"""
    content = TextAreaField('Antwort', validators=[
        DataRequired(message='Antwort ist erforderlich'),
        Length(min=5, message='Antwort muss mindestens 5 Zeichen lang sein')
    ])
    submit = SubmitField('Antworten')

class SearchForm(FlaskForm):
    """Form for searching content"""
    query = StringField('Suche', validators=[
        DataRequired(message='Suchbegriff ist erforderlich'),
        Length(min=3, max=100, message='Suchbegriff muss zwischen 3 und 100 Zeichen lang sein')
    ])
    submit = SubmitField('Suchen')