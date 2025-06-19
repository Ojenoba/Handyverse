from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Optional, Length
from flask_wtf.file import FileField, FileAllowed, FileRequired

class ContactForm(FlaskForm):
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')

class MessageForm(FlaskForm):
    content = TextAreaField('Message', validators=[DataRequired(), Length(min=1, max=1000)])
    submit = SubmitField('Send')

class UploadForm(FlaskForm):
    file = FileField('Profile Picture', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Upload')

class JobPostForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=1000)])
    location = StringField('Location', validators=[Optional(), Length(max=100)])
    budget = StringField('Budget (₦)', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Post Job')