import logging

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView, DeleteView
from django.views.generic.edit import FormView
from tom_observations.models import DynamicCadence

from calibrations.facilities.photometric_standards_facility import PhotometricStandardsManualSubmissionForm
from calibrations.models import Filter, Instrument, InstrumentFilter


logger = logging.getLogger(__name__)


class PhotometricStandardsCadencesList(TemplateView):
    template_name = 'photometric_standards/photometric_standards_cadences_list.html'

    
class PhotometricStandardsCadencesView(TemplateView):
    template_name = 'photometric_standards/photometric_standards_cadences_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sites'] = Instrument.objects.distinct('site').values_list('site', flat=True)
        return context


class PhotometricStandardsCadencesSiteView(TemplateView):
    template_name = 'photometric_standards/photometric_standards_cadences_site_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site = kwargs.get('site')
        instruments_for_site = Instrument.objects.filter(site=site)
        context['site'] = site
        context['instruments'] = instruments_for_site
        return context


# TODO: finish implementation of PhotometricStandardsSubmissionView
class PhotometricStandardsView(FormView):
    template_name = 'photometric_standards/photometric_standards_view.html'
    form_class = PhotometricStandardsManualSubmissionForm
    success_url = reverse_lazy('photometric_standards:photometric_standards_home')

    def form_invalid(self, form):
        messages.error(self.request, f'The photometric standards submission form is invalid: {form.errors}.')
        logger.error(f'Invalid form submission for photometric standards manual submission: {form.errors}.')
        return super().form_invalid(form)

    def form_valid(self, form) -> HttpResponse:
        # This method is called when valid form data has been POSTed.
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial.update({'facility': 'LCO Calibrations'})
        return initial

class PhotometricStandardsForm(FormView):
    template_name = 'photometric_standards/photometric_standards_form.html'
    form_class = PhotometricStandardsManualSubmissionForm
    success_url = reverse_lazy('photometric_standards:photometric_standards_home')

    def form_invalid(self, form):
        messages.error(self.request, f'The photometric standards submission form is invalid: {form.errors}.')
        logger.error(f'Invalid form submission for photometric standards manual submission: {form.errors}.')
        return super().form_invalid(form)

    def form_valid(self, form) -> HttpResponse:
        # This method is called when valid form data has been POSTed.
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial.update({'facility': 'LCO Calibrations'})
        return initial

class PhotometricStandardsTargets(FormView):
    template_name = 'photometric_standards/photometric_standards_targets.html'
    form_class = PhotometricStandardsManualSubmissionForm
    success_url = reverse_lazy('photometric_standards:photometric_standards_home')

    def form_invalid(self, form):
        messages.error(self.request, f'The photometric standards submission form is invalid: {form.errors}.')
        logger.error(f'Invalid form submission for photometric standards manual submission: {form.errors}.')
        return super().form_invalid(form)

    def form_valid(self, form) -> HttpResponse:
        # This method is called when valid form data has been POSTed.
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        initial.update({'facility': 'LCO Calibrations'})
        return initial

class PhotometricStandardsCadenceToggleView(RedirectView):
    pattern_name = 'photometric_standards:photometric_standards_cadences'

    def get_redirect_url(self, *args, **kwargs):
        cadence_id = kwargs.pop('pk', None)
        dc = DynamicCadence.objects.get(pk=cadence_id)
        dc.active = not dc.active
        dc.save()
        return super().get_redirect_url(*args, **kwargs)


class PhotometricStandardsCadenceDeleteView(DeleteView):
    model = DynamicCadence
    success_url = reverse_lazy('photometric_standards:photometric_standards_cadences')
    template_name = 'photometric_standards/dynamiccadence_confirm_delete.html'
