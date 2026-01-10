from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError
from app.models import User

class MessageForm(FlaskForm):
    """Form for sending private messages"""
    recipient = SelectField('Empfänger', coerce=int, validators=[
        DataRequired(message='Empfänger ist erforderlich')
    ])
    subject = StringField('Betreff', validators=[
        DataRequired(message='Betreff ist erforderlich'),
        Length(min=5, max=200, message='Betreff muss zwischen 5 und 200 Zeichen lang sein')
    ])
    content = TextAreaField('Nachricht', validators=[
        DataRequired(message='Nachricht ist erforderlich'),
        Length(min=10, message='Nachricht muss mindestens 10 Zeichen lang sein')
    ])
    submit = SubmitField('Nachricht senden')

    def __init__(self, current_user_id, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)
        # Populate recipient choices (exclude current user)
        users = User.query.filter(User.id != current_user_id, User.is_active == True).all()
        self.recipient.choices = [(user.id, user.username) for user in users]

    def validate_recipient(self, recipient):
        """Validate recipient exists and is active"""
        user = User.query.get(recipient.data)
        if user is None or not user.is_active:
            raise ValidationError('Ungültiger Empfänger')