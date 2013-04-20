# Django DSL Forms

Create basic forms using Django templates to be loaded with ajax.


# Step 1: Set up a url entry to render forms

```
from django.conf.urls import patterns, url 

from dslforms.views import dslform
from myapp.methods import send_form_email


def save_method(form, request, **kwargs):
    send_form_email(form)


urlpatterns = patterns("",
    url(
        regex="^(?P<slug>[^/]+)/$",
        view=dslform,
        kwargs=dict(
            save_method=save_method,
            template_base="dslforms/",
        ),  
    ),  
)
```

You must supply your own `save_method` to process the form data.

The `template_base` folder is where in your templates folder form definitions will go.



# Step 2: Create a form template

Example form: dslforms/myform.html

```
{% block form %}
[field]
name: name
max_length: 100
error: Please enter your name

[field]
name: email
max_length: 100
error: Please enter your email address
widget: email
    
[field]
name: description
max_length: 1000
error: Please enter a description
widget: textarea
{% endblock %}

{% block display %}
  {% if request.GET.c %}
    <h1>Success!</h1>
  {% else %}
    <form method="POST" action="{{ request.path }}">
      {{ form.as_p }}
      <button type="submit">Submit</button>
    </form>
  {% endif %}
{% endblock %}
```

**Notes**

The form definition goes into the `form` block.

The rendering html goes into the `display` block.

Multiple types of fields can be defined. <a href="#form-field-reference">See below for a full reference.</a>


# Step 3: Load the form into a page using ajax

Based on the above url entry, the form will be rendered at /dslforms/myform/.

Below is a sample jQuery plugin to load it with ajax into another page.

**Html**

```
<div data-ajaxform-src="/dslforms/myform/">
  <p class="visible-no-js">Please enable javascript to use this form.</p>
</div>
```

**jQuery plug-in**

```
(function ($) {
    "use strict";

    $("[data-ajaxform-src]").each(function () {
        var $this = $(this);
        var endpoint = $this.attr("data-ajaxform-src");

        $.get(endpoint).done(function (data) {
            $this.html($(data));
        });

        $this.on("submit", "form", function (e) {
            var $form = $(this);
            $.post($form.attr("action"), $form.serialize()).done(function (data) {
                $this.html($(data));
            });
            e.preventDefault();
        });
    });
}(jQuery));
```

## Step 4: Load your page and submit your form

Now you can add or edit simple forms by adding templates in `dslforms/`.


# Sending email with django-email-template

The <a href="https://github.com/prestontimmons/django-email-template">django-email-template</a> packages makes it easy to specify email content and recipients in the form template.

Create a `save_method` like this:

```
from email_template.email import send

def send_entry(form, request, template_name, **kwargs):
    send(request, template_name, dict(form=form, data=form.cleaned_data))
```

Modify the url pattern to use this as the `save_method`:

```
url(
    regex="^(?P<slug>[^/]+)/$",
    view=dslform,
    kwargs=dict(
        save_method=send_entry,
        template_base="dslforms/",
    ),  
)  
```

You can now specify `subject`, `recipients`, and `text` in the same template as your form.

```
{% block subject %}Form submission{% endblock %}

{% block text %}
Name: {{ data.name }}
Email: {{ data.email }}
{% endblock %}

{% block recipients %}mario@bowser.com{% endblock %}
```

# Form Field Reference

The below field types are recognized:

**Text Field**
```
[field]
name: first_name
max_length: 100
```

**Optional Field**
```
[field]
name: phone
max_length: 100
required: False
```

**Textarea**

```
[field]
name: description
max_length: 1000
widget: textarea
```

**Email Field**

```
[field]
name: email
max_length: 200
widget: email
```

**Select Field**

```
[field]
name: category
error: Please choose a category
widget: select
choices: |
  - , -- Choose one --
  - Choice 1
  - Choice 2
  - Choice 3
  - Other
```

**Required Checkbox Field**

```
[field]
name: agree_to_statement
error: You must agree with statement
widget: checkbox
```

**Optional Checkbox Field**

```
[field]
name: receive_email
required: False
widget: checkbox
```
