from datetime import datetime

from tom_targets.models import Target


# this is an extension to tom_targets.models.Target class
#
def target_is_in_season(self, query_date: datetime = datetime.utcnow()):
    """"Returns True if query_date is between target's seasonal_start and seasonal_end
    Note: seasonal_start and seasonal_end are month numbers (1=January, etc).

    This method will be added to the Target class with setattr (that's why it has a self argument).
    """
    seasonal_start = int(self.targetextra_set.filter(key='seasonal_start').first().float_value)
    seasonal_end = int(self.targetextra_set.filter(key='seasonal_end').first().float_value)

    return seasonal_start <= query_date.month <= seasonal_end
setattr(Target, 'target_is_in_season', target_is_in_season)  # noqa - add method to Target class
