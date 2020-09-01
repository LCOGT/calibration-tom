from django.forms import CharField, Form


class CalibrationForm(Form):
    name = CharField()
    site = ChoiceField()