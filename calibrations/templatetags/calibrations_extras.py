from datetime import datetime

from django import template

register = template.Library()


@register.inclusion_tag('calibrations/partials/site_calibration_button.html')
def site_calibration_button(site, instrument):
    """
    Renders a button for creating a new series of calibrations for a given instrument/site.
    """
    return {'site': site, 'instrument': instrument}


@register.simple_tag
def display_seasonal_start_or_end(month):
    return datetime(year=datetime.now().year, month=int(month), day=1).strftime('%B')
