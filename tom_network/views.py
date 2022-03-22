import logging

from datetime import datetime
from io import StringIO
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, QueryDict, StreamingHttpResponse
from django.forms import HiddenInput
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.utils.text import slugify
from django.utils.safestring import mark_safe
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic import RedirectView, TemplateView, View
from django_filters.views import FilterView

from guardian.mixins import PermissionListMixin
from guardian.shortcuts import get_objects_for_user, get_groups_with_perms, assign_perm

from tom_common.hints import add_hint
from tom_common.hooks import run_hook

from tom_observations.observation_template import ApplyObservationTemplateForm
from tom_observations.models import ObservationTemplate

from tom_network.groups import (
    add_all_to_group, add_selected_to_group, remove_all_from_group, remove_selected_from_group,
    move_all_to_group, move_selected_to_group
)
from tom_network.models import Instrument, InstrumentList
from tom_network.utils import import_instruments, export_instruments

logger = logging.getLogger(__name__)


class InstrumentListView(PermissionListMixin, FilterView):
    """
    View for listing instruments in the Calibration-TOM. Requires authorization.
    """
    template_name = 'tom_network/instrument_list.html'
    paginate_by = 25
    strict = False
    model = Instrument
    #filterset_class = InstrumentFilter
    ordering = ['-created']

    def get_context_data(self, *args, **kwargs):
        """
        Adds the number of instruments visible, the available ``InstrumentList`` objects if the user is authenticated, and
        the query string to the context object.

        :returns: context dictionary
        :rtype: dict
        """
        context = super().get_context_data(*args, **kwargs)
        context['instrument_count'] = context['paginator'].count
        # hide instrument group list if user not logged in
        context['groups'] = (InstrumentList.objects.all()
                                if self.request.user.is_authenticated
                                else InstrumentList.objects.none())
        context['query_string'] = self.request.META['QUERY_STRING']
        return context


#class InstrumentCreateView(LoginRequiredMixin, CreateView):
#    """
#    View for creating a Instrument. Requires authentication.
#    """

#    model = Instrument
#    fields = '__all__'

    #def get_default_instrument_type(self):
    #    """
    #    Returns the user-configured instrument type specified in ``settings.py``, if it exists, otherwise returns sidereal
    #
    #    :returns: User-configured instrument type or global default
    #    :rtype: str
    #    """
    #    try:
    #        return settings.INSTRUMENT_TYPE
    #    except AttributeError:
    #        return Instrument.SIDEREAL

#    def get_instrument_type(self):
#        """
#        Gets the type of the instrument to be created from the query parameters. If none exists, use the default instrument
#        type specified in ``settings.py``.

#        :returns: instrument type
#        :rtype: str
#        """
#        obj = self.request.GET or self.request.POST
#        instrument_type = obj.get('instrument_type')
        # If None or some invalid value, use default instrument type
        #if instrument_type not in (Instrument.SIDEREAL, Instrument.NON_SIDEREAL):
        #    instrument_type = self.get_default_instrument_type()
#        return instrument_type

#    def get_initial(self):
#        """
#        Returns the initial data to use for forms on this view.

#        :returns: Dictionary with the following keys:

#                  `type`: ``str``: Type of the instrument to be created

#                  `groups`: ``QuerySet<Group>`` Groups available to the current user

#        :rtype: dict
#        """
#        return {
#            'type': self.get_instrument_type(),
#            'groups': self.request.user.groups.all(),
#            **dict(self.request.GET.items())
#        }

#    def get_context_data(self, **kwargs):
#        """
#        Inserts certain form data into the context dict.

#        :returns: Dictionary with the following keys:

#                  `type_choices`: ``tuple``: Tuple of 2-tuples of strings containing available instrument types in the TOM

#        :rtype: dict
#        """
#        context = super(InstrumentCreateView, self).get_context_data(**kwargs)
#        context['instrument_type_choices'] = Instrument.INSTRUMENT_TYPES
#        return context

#    def get_form_class(self):
#        """
#        Return the form class to use in this view.

#        :returns: form class for instrument creation
#        :rtype: subclass of InstrumentCreateForm
#        """
        #instrument_type = self.get_instrument_type()
        #self.initial['type'] = instrument_type
        
#        return InstrumentCreateForm

#    def form_valid(self, form):
#        """
#        Runs after form validation. Creates the ``Instrument``,
#        then runs the ``instrument_post_save`` hook and redirects to the success URL.

#        :param form: Form data for instrument creation
#        :type form: subclass of InstrumentCreateForm
#        """
#        super().form_valid(form)
        
#        logger.info('Instrument post save hook: %s created: %s', self.object, True)
#        run_hook('instrument_post_save', instrument=self.object, created=True)
#        return redirect(self.get_success_url())

#    def get_form(self, *args, **kwargs):
#        """
#        Gets an instance of the ``InstrumentCreateForm`` and populates it with the groups available to the current user.

#        :returns: instance of creation form
#        :rtype: subclass of InstrumentCreateForm
#        """
#        form = super().get_form(*args, **kwargs)
#        if self.request.user.is_superuser:
#            form.fields['groups'].queryset = Group.objects.all()
#        else:
#            form.fields['groups'].queryset = self.request.user.groups.all()
#        return form


#class InstrumentUpdateView(UpdateView):
#    """
#    View that handles updating as instrument.
#    """
#    permission_required = 'tom_network.change_instrument'
#    model = Instrument
#    fields = '__all__'

#    @transaction.atomic
#    def form_valid(self, form):
#        """
#        Runs after form validation.
#        Calls the superclass implementation of ``form_valid``, which saves the ``Instrument``. If any forms are invalid, rolls back
#        the changes.

#        :param form: Form data for instrument update
#        :type form: subclass of InstrumentCreateForm
#        """
#        form.add_error(None, names.errors)
#        form.add_error(None, names.non_form_errors())
#        return super().form_invalid(form)
#        super().form_valid(form)
#        return redirect(self.get_success_url())

#    def get_queryset(self, *args, **kwargs):
#        """
#        Returns the queryset that will be used to look up the Instrument by limiting the result to instruments that the user is
#        authorized to modify.

#        :returns: Set of instruments
#        :rtype: QuerySet
#        """
#        return get_objects_for_user(self.request.user, 'tom_network.change_instrument')

#    def get_form_class(self):
#        """
#        Return the form class to use in this view.

#        :returns: form class for instrument update
#        :rtype: subclass of InstrumentCreateForm
#        """
        
#        return InstrumentCreateForm

#    def get_initial(self):
#        """
#        Returns the initial data to use for forms on this view. For the ``InstrumentUpdateView``, adds the groups that the
#        instrument is a member of.

#        :returns:
#        :rtype: dict
#        """
#        initial = super().get_initial()
#        initial['groups'] = get_groups_with_perms(self.get_object())
#        return initial

#    def get_form(self, *args, **kwargs):
#        """
#        Gets an instance of the ``InstrumentCreateForm`` and populates it with the groups available to the current user.

#        :returns: instance of creation form
#        :rtype: subclass of InstrumentCreateForm
#        """
#        form = super().get_form(*args, **kwargs)
#        if self.request.user.is_superuser:
#            form.fields['groups'].queryset = Group.objects.all()
#        else:
#            form.fields['groups'].queryset = self.request.user.groups.all()
#        return form


#class InstrumentDeleteView(DeleteView):
#    """
#    View for deleting a instrument. Requires authorization.
#    """
#    permission_required = 'tom_instruments.delete_instrument'
#    success_url = reverse_lazy('instruments:list')
#    model = Instrument


class InstrumentDetailView(DetailView):
    """
    View that handles the display of the instrument details. Requires authorization.
    """
    #permission_required = 'tom_network.view_instrument'
    model = Instrument

    def get_context_data(self, *args, **kwargs):
        """
        Adds the ``DataProductUploadForm`` to the context and prepopulates the hidden fields.

        :returns: context object
        :rtype: dict
        """
        context = super().get_context_data(*args, **kwargs)
        observation_template_form = ApplyObservationTemplateForm(initial={'instrument': self.get_object()})
        if any(self.request.GET.get(x) for x in ['observation_template', 'cadence_strategy', 'cadence_frequency']):
            initial = {'instrument': self.object}
            initial.update(self.request.GET)
            observation_template_form = ApplyObservationTemplateForm(
                initial=initial
            )
        observation_template_form.fields['instrument'].widget = HiddenInput()
        context['observation_template_form'] = observation_template_form
        return context

    def get(self, request, *args, **kwargs):
        """
        Handles the GET requests to this view. If update_status is passed into the query parameters, calls the
        updatestatus management command to query for new statuses for ``ObservationRecord`` objects associated with this
        instrument.

        :param request: the request object passed to this view
        :type request: HTTPRequest
        """
        update_status = request.GET.get('update_status', False)
        if update_status:
            if not request.user.is_authenticated:
                return redirect(reverse('login'))
            instrument_id = kwargs.get('pk', None)
            out = StringIO()
            call_command('updatestatus', instrument_id=instrument_id, stdout=out)
            messages.info(request, out.getvalue())
            add_hint(request, mark_safe(
                              'Did you know updating observation statuses can be automated? Learn how in'
                              '<a href=https://tom-toolkit.readthedocs.io/en/stable/customization/automation.html>'
                              ' the docs.</a>'))
            return redirect(reverse('tom_network:detail', args=(instrument_id,)))

        obs_template_form = ApplyObservationTemplateForm(request.GET)
        if obs_template_form.is_valid():
            obs_template = ObservationTemplate.objects.get(pk=obs_template_form.cleaned_data['observation_template'].id)
            obs_template_params = obs_template.parameters
            obs_template_params['cadence_strategy'] = request.GET.get('cadence_strategy', '')
            obs_template_params['cadence_frequency'] = request.GET.get('cadence_frequency', '')
            params = urlencode(obs_template_params)
            return redirect(
                reverse('tom_observations:create',
                        args=(obs_template.facility,)) + f'?instrument_id={self.get_object().id}&' + params)

        return super().get(request, *args, **kwargs)


#class InstrumentImportView(LoginRequiredMixin, TemplateView):
#    """
#    View that handles the import of instruments from a CSV. Requires authentication.
#    """
#    template_name = 'tom_network/instrument_import.html'

#    def post(self, request):
#        """
#        Handles the POST requests to this view. Creates a StringIO object and passes it to ``import_instruments``.

#        :param request: the request object passed to this view
#        :type request: HTTPRequest
#        """
#        csv_file = request.FILES['instrument_csv']
#        csv_stream = StringIO(csv_file.read().decode('utf-8'), newline=None)
#        result = import_instruments(csv_stream)
#        messages.success(
#            request,
#            'Instruments created: {}'.format(len(result['instruments']))
#        )
#        for error in result['errors']:
#            messages.warning(request, error)
#        return redirect(reverse('tom_network:list'))


#class InstrumentExportView(InstrumentListView):
#    """
#    View that handles the export of instruments to a CSV. Only exports selected instruments.
#    """
#    def render_to_response(self, context, **response_kwargs):
#        """
#        Returns a response containing the exported CSV of selected instruments.

#        :param context: Context object for this view
#        :type context: dict

#        :returns: response class with CSV
#        :rtype: StreamingHttpResponse
#        """
#        qs = context['filter'].qs.values()
#        file_buffer = export_instruments(qs)
#        file_buffer.seek(0)  # goto the beginning of the buffer
#        response = StreamingHttpResponse(file_buffer, content_type="text/csv")
#        filename = "instruments-{}.csv".format(slugify(datetime.utcnow()))
#        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
#        return response


#class InstrumentAddRemoveGroupView(LoginRequiredMixin, View):
#    """
#    View that handles addition and removal of instruments to instrument groups. Requires authentication.
#    """

#    def post(self, request, *args, **kwargs):
#        """
#        Handles the POST requests to this view. Routes the information from the request and query parameters to the
#        appropriate utility method in ``groups.py``.

#        :param request: the request object passed to this view
#        :type request: HTTPRequest
#        """
#        query_string = request.POST.get('query_string', '')
#        group_id = request.POST.get('group')
#        filter_data = QueryDict(query_string)
#        try:
#            group_object = InstrumentList.objects.get(pk=group_id)
#        except Exception as e:
#            messages.error(request, 'Cannot find the instrument group with id={}; {}'.format(group_id, e))
#            return redirect(reverse('tom_network:list') + '?' + query_string)
#        if not request.user.has_perm('tom_network.view_instrumentlist', group_object):
#            messages.error(request, 'Permission denied.')
#            return redirect(reverse('tom_network:list') + '?' + query_string)

#        if 'add' in request.POST:
#            if request.POST.get('isSelectAll') == 'True':
#                add_all_to_group(filter_data, group_object, request)
#            else:
#                instruments_ids = request.POST.getlist('selected-instrument')
#                add_selected_to_group(instruments_ids, group_object, request)
#        if 'remove' in request.POST:
#            if request.POST.get('isSelectAll') == 'True':
#                remove_all_from_group(filter_data, group_object, request)
#            else:
#                instruments_ids = request.POST.getlist('selected-instrument')
#                remove_selected_from_group(instruments_ids, group_object, request)
#        if 'move' in request.POST:
#            if request.POST.get('isSelectAll') == 'True':
#                move_all_to_group(filter_data, group_object, request)
#            else:
#                instrument_ids = request.POST.getlist('selected-instrument')
#                move_selected_to_group(instrument_ids, group_object, request)

#        return redirect(reverse('tom_network:list') + '?' + query_string)


class InstrumentGroupView(PermissionListMixin, ListView):
    """
    View that handles the display of ``InstrumentList`` objects, also known as instrument groups. Requires authorization.
    """
    #permission_required = 'tom_network.view_instrumentlist'
    template_name = 'tom_network/instrument_group.html'
    model = InstrumentList
    paginate_by = 25


#class InstrumentGroupDeleteView(DeleteView):
#    """
#    View that handles the deletion of ``InstrumentList`` objects, also known as instrument groups. Requires authorization.
#    """
#    permission_required = 'tom_network.delete_instrumentlist'
#    model = InstrumentList
#    success_url = reverse_lazy('instruments:instrumentgroup')


#class InstrumentGroupCreateView(LoginRequiredMixin, CreateView):
#    """
#    View that handles the creation of ``InstrumentList`` objects, also known as instrument groups. Requires authentication.
#    """
#    model = InstrumentList
#    fields = ['name']
#    success_url = reverse_lazy('instruments:instrumentgroup')

#    def form_valid(self, form):
#        """
#        Runs after form validation. Saves the instrument group and assigns the user's permissions to the group.

#        :param form: Form data for instrument creation
#        :type form: django.forms.ModelForm
#        """
#        obj = form.save(commit=False)
#        obj.save()
#        assign_perm('tom_network.view_instrumentlist', self.request.user, obj)
#        assign_perm('tom_network.change_instrumentlist', self.request.user, obj)
#        assign_perm('tom_network.delete_instrumentlist', self.request.user, obj)
#        return super().form_valid(form)
