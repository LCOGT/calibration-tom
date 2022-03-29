from .models import Instrument
from django.contrib import messages


def add_all_to_group(filter_data, group_object, request):
    """
    Adds all instruments displayed by a particular filter to a ``InstrumentList``. Successes, warnings, and errors result in
    messages being added to the request with the appropriate message level.

    :param filter_data: instrument filter data passed to the calling view
    :type filter_data: django.http.QueryDict

    :param group_object: ``InstrumentList`` to add instruments to
    :type group_object: InstrumentList

    :param request: request object passed to the calling view
    :type request: HTTPRequest
    """
    success_instruments = []
    warning_instruments = []  # instruments that are already in the group
    failure_instruments = []
    try:
        instrument_queryset = InstrumentFilter(request=request, data=filter_data, queryset=Instrument.objects.all()).qs
    except Exception:
        messages.error(request, "Error with filter parameters. No instrument(s) were added to group '{}'."
                                .format(group_object.name))
        return
    for instrument_object in instrument_queryset:
        try:
            if not request.user.has_perm('network.change_instrument', instrument_object):
                failure_instruments.append((instrument_object.name, 'Permission denied.',))
            elif instrument_object in group_object.instruments.all():
                warning_instruments.append(instrument_object.name)
            else:
                group_object.instruments.add(instrument_object)
                success_instruments.append(instrument_object.name)
        except Exception as e:
            failure_instruments.append((instrument_object.pk, e,))
    messages.success(request, "{} instrument(s) successfully added to group '{}'."
                              .format(len(success_instruments), group_object.name))
    if warning_instruments:
        messages.warning(request, "{} instrument(s) already in group '{}': {}"
                                  .format(len(warning_instruments), group_object.name, ', '.join(warning_instruments)))
    for failure_instrument in failure_instruments:
        messages.error(request, "Failed to add instrument with id={} to group '{}'; {}"
                                .format(failure_instrument[0], group_object.name, failure_instrument[1]))


def add_selected_to_group(instruments_ids, group_object, request):
    """
    Adds all selected instruments to a ``InstrumentList``. Successes, warnings, and errors result in messages being added to the
    request with the appropriate message level.

    :param instruments_ids: list of selected instruments
    :type instruments_ids: list

    :param group_object: ``InstrumentList`` to add instruments to
    :type group_object: InstrumentList

    :param request: request object passed to the calling view
    :type request: HTTPRequest
    """
    success_instruments = []
    warning_instruments = []
    failure_instruments = []
    for instrument_id in instruments_ids:
        try:
            instrument_object = Instrument.objects.get(pk=instrument_id)
            if not request.user.has_perm('network.change_instrument', instrument_object):
                failure_instruments.append((instrument_object.name, 'Permission denied.',))
            elif instrument_object in group_object.instruments.all():
                warning_instruments.append(instrument_object.name)
            else:
                group_object.instruments.add(instrument_object)
                success_instruments.append(instrument_object.name)
        except Exception as e:
            failure_instruments.append((instrument_object.pk, e,))
    messages.success(request, "{} instrument(s) successfully added to group '{}'."
                              .format(len(success_instruments), group_object.name))
    if warning_instruments:
        messages.warning(request, "{} instrument(s) already in group '{}': {}"
                                  .format(len(warning_instruments), group_object.name, ', '.join(warning_instruments)))
    for failure_instrument in failure_instruments:
        messages.error(request, "Failed to add instrument with id={} to group '{}'; {}"
                                .format(failure_instrument[0], group_object.name, failure_instrument[1]))


def remove_all_from_group(filter_data, group_object, request):
    """
    Removes all instruments displayed by a particular filter from a ``InstrumentList``. Successes, warnings, and errors result
    in messages being added to the request with the appropriate message level.

    :param filter_data: instrument filter data passed to the calling view
    :type filter_data: django.http.QueryDict

    :param group_object: ``InstrumentList`` to remove instruments from
    :type group_object: InstrumentList

    :param request: request object passed to the calling view
    :type request: HTTPRequest
    """
    success_instruments = []
    warning_instruments = []
    failure_instruments = []
    try:
        instrument_queryset = InstrumentFilter(request=request, data=filter_data, queryset=Instrument.objects.all()).qs
    except Exception:
        messages.error(request, "Error with filter parameters. No instrument(s) were removed from group '{}'."
                                .format(group_object.name))
        return
    for instrument_object in instrument_queryset:
        try:
            if not request.user.has_perm('network.change_instrument', instrument_object):
                failure_instruments.append((instrument_object.name, 'Permission denied.',))
            elif instrument_object not in group_object.instruments.all():
                warning_instruments.append(instrument_object.name)
            else:
                group_object.instruments.remove(instrument_object)
                success_instruments.append(instrument_object.name)
        except Exception as e:
            failure_instruments.append({'name': instrument_object.name, 'error': e})
    messages.success(request, "{} instrument(s) successfully removed from group '{}'."
                              .format(len(success_instruments), group_object.name))
    if warning_instruments:
        messages.warning(request, "{} instrument(s) not in group '{}': {}"
                                  .format(len(warning_instruments), group_object.name, ', '.join(warning_instruments)))
    for failure_instrument in failure_instruments:
        messages.error(request, "Failed to remove instrument with id={} from group '{}'; {}"
                                .format(failure_instrument['id'], group_object.name, failure_instrument['error']))


def remove_selected_from_group(instruments_ids, group_object, request):
    """
    Removes all instruments displayed by a particular filter from a ``InstrumentList``. Successes, warnings, and errors result
    in messages being added to the request with the appropriate message level.

    :param instruments_ids: list of selected instruments
    :type instruments_ids: list

    :param group_object: ``InstrumentList`` to remove instruments from
    :type group_object: InstrumentList

    :param request: request object passed to the calling view
    :type request: HTTPRequest
    """
    success_instruments = []
    warning_instruments = []
    failure_instruments = []
    for instrument_id in instruments_ids:
        try:
            instrument_object = Instrument.objects.get(pk=instrument_id)
            if not request.user.has_perm('network.change_instrument', instrument_object):
                failure_instruments.append((instrument_object.name, 'Permission denied.',))
            elif instrument_object not in group_object.instruments.all():
                warning_instruments.append(instrument_object.name)
            else:
                group_object.instruments.remove(instrument_object)
                success_instruments.append(instrument_object.name)
        except Exception as e:
            failure_instruments.append({'id': instrument_id, 'error': e})
    messages.success(request, "{} instrument(s) successfully removed from group '{}'."
                              .format(len(success_instruments), group_object.name))
    if warning_instruments:
        messages.warning(request, "{} instrument(s) not in group '{}': {}"
                                  .format(len(warning_instruments), group_object.name, ', '.join(warning_instruments)))
    for failure_instrument in failure_instruments:
        messages.error(request, "Failed to remove instrument with id={} from group '{}'; {}"
                                .format(failure_instrument['id'], group_object.name, failure_instrument['error']))


def move_all_to_group(filter_data, group_object, request):
    """
    Moves all instruments displayed by a particular filter to a ``InstrumentList`` by removing all previous gropupings
    and then adding them to the supplied group_object.
    Successes, warnings, and errors result
    in messages being added to the request with the appropriate message level.

    :param filter_data: instrument filter data passed to the calling view
    :type filter_data: django.http.QueryDict

    :param group_object: ``InstrumentList`` to add instruments to
    :type group_object: InstrumentList

    :param request: request object passed to the calling view
    :type request: HTTPRequest
    """
    success_instruments = []
    warning_instruments = []
    failure_instruments = []
    try:
        instrument_queryset = InstrumentFilter(request=request, data=filter_data, queryset=Instrument.objects.all()).qs
    except Exception:
        messages.error(request, "Error with filter parameters. No instrument(s) were moved to group '{}'."
                                .format(group_object.name))
        return
    for instrument_object in instrument_queryset:
        try:
            if not request.user.has_perm('network.change_instrument', instrument_object):
                failure_instruments.append((instrument_object.name, 'Permission denied.',))
            elif instrument_object in group_object.instruments.all():
                warning_instruments.append(instrument_object.name)
            else:
                instrument_object.instrumentlist_set.clear()
                group_object.instruments.add(instrument_object)
                success_instruments.append(instrument_object.name)
        except Exception as e:
            failure_instruments.append({'name': instrument_object.name, 'error': e})
    messages.success(request, "{} instrument(s) successfully moved to group '{}'."
                              .format(len(success_instruments), group_object.name))
    if warning_instruments:
        messages.warning(request, "{} instrument(s) already in group '{}': {}"
                                  .format(len(warning_instruments), group_object.name, ', '.join(warning_instruments)))
    for failure_instrument in failure_instruments:
        messages.error(request, "Failed to move instrument with id={} to group '{}'; {}"
                                .format(failure_instrument['id'], group_object.name, failure_instrument['error']))


def move_selected_to_group(instruments_ids, group_object, request):
    """
    Moves all selected instruments to a ``InstrumentList`` by removing them from their previous groups
    and then adding them to the supplied group_object.
    Successes, warnings, and errors result in messages being added to the
    request with the appropriate message level.

    :param instruments_ids: list of selected instruments
    :type instruments_ids: list

    :param group_object: ``InstrumentList`` to add instruments to
    :type group_object: InstrumentList

    :param request: request object passed to the calling view
    :type request: HTTPRequest
    """
    success_instruments = []
    warning_instruments = []
    failure_instruments = []
    for instrument_id in instruments_ids:
        try:
            instrument_object = Instrument.objects.get(pk=instrument_id)
            if not request.user.has_perm('network.change_instrument', instrument_object):
                failure_instruments.append((instrument_object.name, 'Permission denied.',))
            elif instrument_object in group_object.instruments.all():
                warning_instruments.append(instrument_object.name)
            else:
                instrument_object.instrumentlist_set.clear()
                group_object.instruments.add(instrument_object)
                success_instruments.append(instrument_object.name)
        except Exception as e:
            failure_instruments.append((instrument_id, e,))
    messages.success(request, "{} instrument(s) successfully moved to group '{}'."
                              .format(len(success_instruments), group_object.name))
    if warning_instruments:
        messages.warning(request, "{} instrument(s) already in group '{}': {}"
                                  .format(len(warning_instruments), group_object.name, ', '.join(warning_instruments)))
    for failure_instrument in failure_instruments:
        messages.error(request, "Failed to move instrument with id={} to group '{}'; {}"
                                .format(failure_instrument[0], group_object.name, failure_instrument[1]))
