import unittest

from django import forms


def generate_fields(serialized):
    for field in serialized:
        kwargs = dict(
            max_length=field.get("max_length", 100),
            required=field.get("required", True),
        )

        if "error" in field:
            kwargs["error_messages"] = dict(
                required=field["error"],
            )

        if "label" in field:
            kwargs["label"] = field["label"]

        widget = field.get("widget", "charfield")

        if widget == "select":
            kwargs["choices"] = field["choices"]

            kwargs.pop("max_length", "")

            yield field["name"], forms.ChoiceField(**kwargs)
            continue

        if widget == "checkbox":
            kwargs.pop("max_length", "")
            yield field["name"], forms.BooleanField(**kwargs)

        if widget == "textarea":
            kwargs["widget"] = forms.Textarea
            yield field["name"], forms.CharField(**kwargs)

        if widget == "charfield":
            yield field["name"], forms.CharField(**kwargs)

        if widget == "email":
            yield field["name"], forms.EmailField(**kwargs)


def form_class_factory(fields, base=(forms.BaseForm, )):
    form_fields = dict(generate_fields(fields))
    return type("Form", base, dict(base_fields=form_fields))



class FormClassFactoryTest(unittest.TestCase):

    def test_charfield(self):
        form_class = form_class_factory([{
            "max_length": 100,
            "name": "name",
            "error": "Please enter your name",
        }])

        fields = form_class().fields

        self.assertEqual(fields["name"].max_length, 100)
        self.assertEqual(fields["name"].error_messages["required"],
            "Please enter your name",
        )
        self.assertEqual(fields["name"].required, True)

    def test_emailfield(self):
        form_class = form_class_factory([{
            "max_length": 100,
            "name": "email",
            "error": "Please enter your email",
            "widget": "email"
        }])

        fields = form_class().fields

        self.assertEqual(fields["email"].max_length, 100)
        self.assertEqual(fields["email"].error_messages["required"],
            "Please enter your email",
        )
        self.assertEqual(fields["email"].__class__.__name__, "EmailField")

    def test_required(self):
        form_class = form_class_factory([{
            "max_length": 100,
            "name": "name",
            "error": "Please enter your name",
            "required": False
        }])

        fields = form_class().fields

        self.assertEqual(fields["name"].required, False)

    def test_choices(self):
        form_class = form_class_factory([{
            "name": "gender",
            "choices": [
                ("", "-- Please Choose --"),
                ("M", "Male"),
                ("F", "Female")
            ],
            "widget": "select",
        }])

        fields = form_class().fields

        self.assertEqual(fields["gender"].choices[0],
            ("", "-- Please Choose --"),
        )
        self.assertEqual(fields["gender"].choices[1],
            ("M", "Male"),
        )

    def test_checkbox(self):
        form_class = form_class_factory([{
            "name": "agree",
            "widget": "checkbox",
            "error": "You must agree",
        }])

        fields = form_class().fields

        self.assertEqual(fields["agree"].required, True)
        self.assertEqual(fields["agree"].__class__.__name__, "BooleanField")
        self.assertEqual(fields["agree"].error_messages["required"],
            "You must agree",
        )

    def test_label(self):
        form_class = form_class_factory([{
            "max_length": 100,
            "name": "name",
            "label": "Full Name",
        }])

        fields = form_class().fields

        self.assertEqual(fields["name"].label, "Full Name")


if __name__ == "__main__":
    unittest.main()
