from os.path import join

from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.template import RequestContext, TemplateDoesNotExist
from django.template.loader import get_template

from .dsl import parse
from .forms import form_class_factory
from .util import render_node


def dslform(request, slug, template_base, save_method, **kwargs):
    confirm_url = request.path + "?c=1"

    template_name = join(template_base, "{0}.html".format(slug))

    try:
        template = get_template(template_name)
    except TemplateDoesNotExist:
        raise Http404("Form template does not exist")

    dsl = render_node(template, "form", RequestContext(request, kwargs))

    if not dsl:
        raise Exception("Missing form block")

    form_class = form_class_factory(parse(dsl))

    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            result = save_method(form, request,
                template_name=template_name, **kwargs)
            response = redirect(confirm_url)
            response.context_data = dict(
                form=form,
                result=result,
            )
            return response
    else:
        form = form_class()

    content = render_node(template, "display", 
        RequestContext(request, dict(form=form, **kwargs)),
    )

    if not content:
        raise Exception("Missing display block")

    response = HttpResponse(content)
    response.context_data = dict(form=form, **kwargs)
    return response
