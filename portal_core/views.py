from django.shortcuts import render
from django.views.generic import TemplateView

class PortalHomeView(TemplateView):
    template_name = 'index.html'
