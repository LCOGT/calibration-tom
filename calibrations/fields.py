import logging

from django import forms

logger = logging.getLogger(__name__)


class FilterMultiWidget(forms.MultiWidget):
    """Set up a checkbox and two integer widgets for the FilterMultiValueField
    """
    def __init__(self, attrs=None):
        widgets = [
            forms.CheckboxInput(attrs=attrs),  # to select the filter
            forms.NumberInput(attrs=attrs),  # for the exposure_count
            forms.NumberInput(attrs=attrs),  # for the exposure_time
        ]
        super().__init__(widgets, attrs)
        # re-assign widgets_name after the __init__ (or else they'll be overridden)
        self.widgets_names = [
            '_selected',
            '_exposure_count',
            '_exposure_time',
        ]

    def decompress(self, value) -> []:
        """Split the combined value of the form MultiValueField into the values for each widget"""

        logger.debug(f'FilterMultiWidget decompress value: {value}')
        if value:
            return [v for v in value.values()]
        return [None, None, None]


class FilterMultiValueField(forms.MultiValueField):

    def compress(self, data_list):
        """Combine cleaned field values in a single value"""
        # logger.debug(f'FilterMultiValueField.compress data_list: {data_list}')
        return data_list

    def __init__(self, **kwargs):
        filter = kwargs.pop('filter')  # Filter model object instance
        required = kwargs.get('required', False)  # don't pop so it gets sent to super via kwargs
        # Define one message for all fields.
        error_messages = {
            'incomplete': f'Exposure time and count must be greater than zero for selected filter: {filter.name}',
        }

        # Or define a different message for each field.
        fields = (
            # add the filter to the instrument_config if checkbox is checked
            forms.BooleanField(required=required),
            # exposure_count
            forms.IntegerField(
                min_value=0, label=True,
                widget=forms.NumberInput(attrs={'placeholder': 'Exposure Count (exposures)'}),
                required=required
            ),
            # exposure_time
            forms.IntegerField(
                min_value=0, label=True,
                widget=forms.NumberInput(attrs={'placeholder': 'Exposure Time (seconds)'}),
                required=required
            ),
        )

        self.widget = FilterMultiWidget()

        super().__init__(
            error_messages=error_messages, fields=fields,
            require_all_fields=False,
            **kwargs  # required is part of the kwargs
        )
