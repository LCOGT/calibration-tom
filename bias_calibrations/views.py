import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView, DeleteView
from django.views.generic.edit import FormView, CreateView
from tom_observations.models import DynamicCadence

from calibrations.facilities.bias_calibrations_facility import BiasCalibrationsManualSubmissionForm
from calibrations.models import Filter, Instrument, InstrumentFilter

from .models import BiasTarget
from .forms import HourAngleTargetCreateForm


logger = logging.getLogger(__name__)

class BiasTargetCreateView(LoginRequiredMixin, CreateView):
    """
    View for creating a Target. Requires authentication.
    """

    model = BiasTarget
    fields = '__all__'

    def get_default_target_type(self):
        """
        Returns the user-configured target type specified in ``settings.py``, if it exists, otherwise returns hour_angle

        :returns: User-configured target type or global default
        :rtype: str
        """
        try:
            return settings.BIAS_TARGET_TYPE
        except AttributeError:
            return BiasTarget.HOUR_ANGLE

    def get_target_type(self):
        """
        Gets the type of the target to be created from the query parameters. If none exists, use the default target
        type specified in ``settings.py``.

        :returns: target type
        :rtype: str
        """
        obj = self.request.GET or self.request.POST
        target_type = obj.get('type')
        # If None or some invalid value, use default target type
        if target_type not in (BiasTarget.HOUR_ANGLE):
            target_type = self.get_default_target_type()
        return target_type

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.

        :returns: Dictionary with the following keys:

                  `type`: ``str``: Type of the target to be created

                  `groups`: ``QuerySet<Group>`` Groups available to the current user

        :rtype: dict
        """
        return {
            'type': self.get_target_type(),
            'groups': self.request.user.groups.all(),
            **dict(self.request.GET.items())
        }

    def get_form_class(self):
        """
        Return the form class to use in this view.

        :returns: form class for target creation
        :rtype: subclass of TargetCreateForm
        """
        target_type = self.get_target_type()
        self.initial['type'] = target_type
        if target_type == BiasTarget.HOUR_ANGLE:

            return HourAngleTargetCreateForm


    def form_valid(self, form):
        """
        Runs after form validation. Creates the ``BiasTarget``, and creates any ``TargetName`` or ``TargetExtra`` objects,
        then runs the ``target_post_save`` hook and redirects to the success URL.

        :param form: Form data for target creation
        :type form: subclass of TargetCreateForm
        """
        super().form_valid(form)
        extra = TargetExtraFormset(self.request.POST)
        names = TargetNamesFormset(self.request.POST)
        if extra.is_valid() and names.is_valid():
            extra.instance = self.object
            extra.save()
            names.instance = self.object
            names.save()
        else:
            form.add_error(None, extra.errors)
            form.add_error(None, extra.non_form_errors())
            form.add_error(None, names.errors)
            form.add_error(None, names.non_form_errors())
            return super().form_invalid(form)

        logger.info('Target post save hook: %s created: %s', self.object, True)
        run_hook('target_post_save', target=self.object, created=True)
        return redirect(self.get_success_url())

    def get_form(self, *args, **kwargs):
        """
        Gets an instance of the ``TargetCreateForm`` and populates it with the groups available to the current user.

        :returns: instance of creation form
        :rtype: subclass of TargetCreateForm
        """
        form = super().get_form(*args, **kwargs)
        if self.request.user.is_superuser:
            form.fields['groups'].queryset = Group.objects.all()
        else:
            form.fields['groups'].queryset = self.request.user.groups.all()
        return form


class BiasCalibrationsCadencesList(TemplateView):
    template_name = 'bias_calibrations/bias_calibrations_cadences_list.html'

    
class BiasCalibrationsCadencesView(TemplateView):
    template_name = 'bias_calibrations/bias_calibrations_cadences_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sites'] = Instrument.objects.distinct('site').values_list('site', flat=True)
        return context


class BiasCalibrationsCadencesSiteView(TemplateView):
    template_name = 'bias_calibrations/bias_calibrations_cadences_site_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site = kwargs.get('site')
        instruments_for_site = Instrument.objects.filter(site=site)
        context['site'] = site
        context['instruments'] = instruments_for_site
        return context


# TODO: finish implementation of BiasCalibrationsSubmissionView
class BiasCalibrationsView(FormView):
    template_name = 'bias_calibrations/bias_calibrations_view.html'
    form_class = BiasCalibrationsManualSubmissionForm
    success_url = reverse_lazy('bias_calibrations:bias_calibrations_home')

    def form_invalid(self, form):
        messages.error(self.request, f'The bias calibrations submission form is invalid: {form.errors}.')
        logger.error(f'Invalid form submission for bias calibrations manual submission: {form.errors}.')
        return super().form_invalid(form)

    def form_valid(self, form) -> HttpResponse:
        # This method is called when valid form data has been POSTed.
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial.update({'facility': 'LCO Calibrations'})
        return initial

class BiasCalibrationsForm(FormView):
    template_name = 'bias_calibrations/bias_calibrations_form.html'
    form_class = BiasCalibrationsManualSubmissionForm
    success_url = reverse_lazy('bias_calibrations:bias_calibrations_home')

    def form_invalid(self, form):
        messages.error(self.request, f'The bias calibrations submission form is invalid: {form.errors}.')
        logger.error(f'Invalid form submission for bias calibrations manual submission: {form.errors}.')
        return super().form_invalid(form)

    def form_valid(self, form) -> HttpResponse:
        # This method is called when valid form data has been POSTed.
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial.update({'facility': 'LCO Calibrations'})
        return initial

class BiasCalibrationsTargets(FormView):
    template_name = 'bias_calibrations/bias_calibrations_targets.html'
    form_class = BiasCalibrationsManualSubmissionForm
    success_url = reverse_lazy('bias_calibrations:bias_calibrations_home')

    def form_invalid(self, form):
        messages.error(self.request, f'The bias calibrations submission form is invalid: {form.errors}.')
        logger.error(f'Invalid form submission for bias calibrations manual submission: {form.errors}.')
        return super().form_invalid(form)

    def form_valid(self, form) -> HttpResponse:
        # This method is called when valid form data has been POSTed.
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial.update({'facility': 'LCO Calibrations'})
        return initial

class BiasCalibrationsCadenceToggleView(RedirectView):
    pattern_name = 'bias_calibrations:bias_calibrations_cadences'

    def get_redirect_url(self, *args, **kwargs):
        cadence_id = kwargs.pop('pk', None)
        dc = DynamicCadence.objects.get(pk=cadence_id)
        dc.active = not dc.active
        dc.save()
        return super().get_redirect_url(*args, **kwargs)


class BiasCalibrationsCadenceDeleteView(DeleteView):
    model = DynamicCadence
    success_url = reverse_lazy('bias_calibrations:bias_calibrations_cadences')
    template_name = 'bias_calibrations/dynamiccadence_confirm_delete.html'
