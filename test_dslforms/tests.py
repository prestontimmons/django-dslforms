from django.http import Http404
from django.template import Template
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import (
    setup_test_template_loader,
    restore_template_loaders,
)

from dslforms.views import dslform


class DslFormTest(TestCase):

    def setUp(self):
        templates = {
            "dslforms/form.html": template_form,
            "dslforms/missing-form.html": template_missing_form,
            "dslforms/missing-display.html": template_missing_display,
        }
        setup_test_template_loader(templates)
 
    def tearDown(self):
        restore_template_loaders()

    def test_get(self):
        request = RequestFactory().get("/dslform/form/")
        response = dslform(request, "form", "dslforms/", save_method)
        self.assertEqual(response.status_code, 200)

        form = response.context_data["form"]
        self.assertEqual(form.fields["name"].max_length, 100)

    def test_post(self):
        request = RequestFactory().post("/dslform/form/", dict(name="Name"))
        response = dslform(request, "form", "dslforms/", save_method)
        self.assertEqual(response.status_code, 302)
        self.assertTrue("form" in response.context_data)
        self.assertEqual(response.context_data["result"], "Saved")

    def test_error(self):
        request = RequestFactory().post("/dslform/form/")
        response = dslform(request, "form", "dslforms/", save_method)
        self.assertEqual(response.status_code, 200)

        form = response.context_data["form"]
        self.assertEqual(form.errors["name"][0], "Please enter your name")

    def test_404(self):
        request = RequestFactory().get("/dslform/form404/")
        with self.assertRaises(Http404):
            dslform(request, "form404", "dslforms/", save_method)

    def test_missing_form_block(self):
        request = RequestFactory().get("/dslform/missing-form/")
        with self.assertRaises(Exception):
            dslform(request, "missing-form", "dslforms/", save_method)

    def test_missing_display_block(self):
        request = RequestFactory().get("/dslform/missing-display/")
        with self.assertRaises(Exception):
            dslform(request, "missing-display", "dslforms/", save_method)


template_form = Template("""
{% block form %}
[field]
name: name
max_length: 100
error: Please enter your name
{% endblock %}

{% block display %}
  {{ form.as_p }}
{% endblock %}
""")


template_missing_form = Template("""
{% block display %}
  {{ form.as_p }}
{% endblock %}
""")


template_missing_display = Template("""
{% block form %}
[field]
name: name
max_length: 100
error: Please enter your name
{% endblock %}
""")


def save_method(form, request, **kwargs):
    return "Saved"


from dslforms.dsl import FormParserTest
from dslforms.forms import FormClassFactoryTest
