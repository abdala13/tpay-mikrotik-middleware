from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, URL, Optional

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[Optional(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    submit = SubmitField("Create account")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class AuditForm(FlaskForm):
    url = StringField("Website URL", validators=[DataRequired(), Length(max=1200)])
    submit = SubmitField("Run audit")

class PlanForm(FlaskForm):
    plan_name = SelectField("Plan", choices=[("Free","Free"),("Starter","Starter"),("Pro","Pro"),("Agency","Agency")])
    submit = SubmitField("Update plan")
