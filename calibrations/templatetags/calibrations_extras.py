from django import template

register = template.Library()


@register.inclusion_tag('calibrations/partials/site_calibration_button.html')
def site_calibration_button(site, instrument):
    """
    Renders a button for creating a new series of calibrations for a given instrument/site.
    """
    return {'site': site, 'instrument': instrument}
