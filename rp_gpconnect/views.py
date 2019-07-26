from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView

from rp_gpconnect.forms import ContactImportForm
from rp_gpconnect.models import ContactImport


class ContactImportView(LoginRequiredMixin, CreateView):
    model = ContactImport
    form_class = ContactImportForm
    template_name = "gpconnect/contact_import_form.html"
    success_url = reverse_lazy("contact_import")
    login_url = "/admin/login/"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super(ContactImportView, self).form_valid(form)
