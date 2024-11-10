from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, Length, NumberRange, ValidationError
from wtforms import StringField, SelectField, IntegerField, SelectMultipleField, SubmitField
from app.constants import DEPARTURE_CHOICES, COUNTRY_CHOICES, CURRENCY_CHOICES

STRING_FIELD_STYLE = "width: 40%; height: 33px; margin: auto; display: block"
TEXT_AREA_STYLE = "width: 40%; height: 100px; margin: auto; display: block"
SELECT_MULTIPLE_STYLE = "width: 40%; height: 200px; margin: auto; display: block"
SUBMIT_STYLE = "margin-bottom: 10px"

class ValidateMaxNightsGreaterThanMin:
    def __init__(self, message=None):
        if not message:
            message = 'Maximum nights must be greater than minimum nights.'
        self.message = message

    def __call__(self, form, field):
        min_nights = form.min_nights.data
        max_nights = field.data
        if max_nights <= min_nights:
            raise ValidationError(self.message)


class AirNomadSocietyForm(FlaskForm):
    username = StringField(label="Username", validators=[DataRequired(), Length(min=3, max=20, message="Set a username within 3 - 8 characters.")], render_kw={"style": f"{STRING_FIELD_STYLE}"})
    email = StringField(label="Email", validators=[DataRequired(), Email()], render_kw={"style": f"{STRING_FIELD_STYLE}"})
    departure_city = SelectField(label="Departure City", choices=DEPARTURE_CHOICES, validators=[DataRequired()], render_kw={"style": f"{STRING_FIELD_STYLE}"})
    currency = SelectField(label="Currency", choices=CURRENCY_CHOICES, validators=[DataRequired()], render_kw={"style": f"{STRING_FIELD_STYLE}"})
    min_nights = IntegerField(label="Minimum Nights", validators=[DataRequired(), NumberRange(min=1, message="Set to 1 or above.")], render_kw={"style": f"{STRING_FIELD_STYLE}"})
    max_nights = IntegerField(label="Maximum Nights", validators=[DataRequired(), NumberRange(min=1, max=180, message="Set to 180 or lower."), ValidateMaxNightsGreaterThanMin()], render_kw={"style": f"{STRING_FIELD_STYLE}"})
    favorite_countries = SelectMultipleField(label="Favorite destinations", choices=COUNTRY_CHOICES, validators=[DataRequired()], render_kw={"style": f"{SELECT_MULTIPLE_STYLE}; f{SUBMIT_STYLE}"})
    join = SubmitField(label="Join Air Nomad Society")
    update = SubmitField(label="Update Preferences")
