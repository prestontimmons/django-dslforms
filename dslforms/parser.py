#  coding=utf-8

import unittest

from rply import LexerGenerator, ParserGenerator
from rply.errors import LexingError

lg = LexerGenerator()

lg.ignore(r"\s+")
lg.ignore(r"\# .*")

lg.add("FIELD", r"\[field\]")
lg.add("CHOICE_HEADER", r"choices: ?\|")
lg.add("ATTRIBUTE", r".+?:.+")
lg.add("CHOICE", r"-.+")

lexer = lg.build()
pg = ParserGenerator([rule.name for rule in lg.rules], cache_id="dslforms")


@pg.production("main : fields")
def main(p):
    return p[0]


@pg.production("fields : fields field")
def fields(p):
    return p[0] + [p[1]]


@pg.production("fields : field")
def fields_single(p):
    return p


@pg.production("field : FIELD attributes")
def field(p):
    return p[1]


@pg.production("attributes : attributes attribute")
def attributes(p):
    return p[0] + [p[1]]


@pg.production("attributes : attribute")
def attributes_single(p):
    return p


@pg.production("attribute : ATTRIBUTE")
def attribute(p):
    val = p[0].getstr().decode("utf-8").split(":")
    return (val[0].strip(), u"".join(val[1:]).strip())


@pg.production("attribute : choice_set")
def attribute_choice_set(p):
    return ("choices", p[0])


@pg.production("choice_set : choice_header choice_list")
def choice_set(p):
    return p[1]


@pg.production("choice_header : CHOICE_HEADER")
def choice_header(p):
    return p


@pg.production("choice_list : choice_tuples")
def choice_list(p):
    return p[0]


@pg.production("choice_tuples : choice_tuples choice_tuple")
def choice_tuples(p):
    return p[0] + [p[1]]


@pg.production("choice_tuples : choice_tuple")
def choice_tuples_single(p):
    return p


@pg.production("choice_tuple : CHOICE")
def choice_tuple(p):
    val = p[0].getstr().strip()[1:].decode("utf-8")

    if "," not in val:
        val = u"%s, %s" % (val, val)

    val = val.split(u",")

    val = (val[0].strip(), u"".join(val[1:]).strip())
    return val


@pg.error
def error_handler(token):
    if token.value == "$end":
        raise EmptyError()
    msg = "Error on line %s. Ran into a %s where it wasn't expected."
    raise ValueError(msg % (token.source_pos.lineno, token.gettokentype()))


class EmptyError(ValueError):
    pass


parser = pg.build()


def format_error(value, e):
    pos = e.source_pos.idx

    marked = value[:pos] + "__posmark__" + value[pos:]
    split = marked.split("\n")
    line_no = 1
    line_text = ""

    for i, line in enumerate(split):
        if "__posmark__" in line:
            line_no = i + 1
            line_text = line.replace("__posmark__", "")

    return "Syntax error on line %s: '%s'" % (
        line_no, line_text,
    )


def clean_fields(fields):
    for field in fields:
        if not field.get("name"):
            raise ValueError(
                "Field must include name attribute",
            )

        if field.get("widget", "charfield") in ["charfield", "textarea"]:
            if not field.get("max_length"):
                raise ValueError(
                    "Field %s must specify max_length" % field["name"],
                )

        field["required"] = field.get("required", "True")
        if field["required"].lower() not in ["true", "false"]:
            raise ValueError(
                "Field %s required attribute must one one of True or False" % field["name"],  # noqa
            )

        if field["required"].lower() == "true":
            field["required"] = True
        else:
            field["required"] = False

        if "max_length" in field:
            field["max_length"] = int(field["max_length"])

    return fields


def parse(value):
    tokens = lexer.lex(value)

    try:
        parsed = parser.parse(tokens)
    except LexingError as e:
        msg = format_error(value, e)
        raise ValueError(msg)

    fields = [dict(x) for x in parsed]

    return clean_fields(fields)


class FormParserTest(unittest.TestCase):

    def test_parser(self):
        text = """
        # comment

        [field]
        name: name
        max_length: 100
        error: Please enter your name ☂

        [field]
        name: email
        max_length: 100
        error: Please enter your email
        testing: testing

        [field]
        name: password
        max_length: 100
        error: Please enter your password
        """

        result = parse(text)
        self.assertEqual(result[0]["name"], "name")
        self.assertEqual(result[0]["max_length"], 100)
        self.assertEqual(result[0]["error"], u"Please enter your name ☂")

        self.assertEqual(result[1]["name"], "email")
        self.assertEqual(result[1]["required"], True)
        self.assertEqual(result[1]["testing"], "testing")

        self.assertEqual(result[2]["name"], "password")

    def test_required_false(self):
        text = """
        [field]
        name: city
        max_length: 80
        required: False
        """

        result = parse(text)
        self.assertEqual(result[0]["name"], "city")
        self.assertEqual(result[0]["max_length"], 80)
        self.assertEqual(result[0]["required"], False)

    def test_choices(self):
        text = """
        [field]
        name: category
        required: True
        choices: |
            - , -- Please Choose --
            - Sponsorship
            - My Account
            - M, Male
            - F, Female
            - à, à choice
        widget: select
        """

        result = parse(text)
        self.assertEqual(result[0]["name"], "category")
        self.assertEqual(result[0]["required"], True)
        self.assertEqual(result[0]["widget"], "select")
        self.assertEqual(
            result[0]["choices"][0],
            ("", "-- Please Choose --"),
        )
        self.assertEqual(
            result[0]["choices"][1],
            ("Sponsorship", "Sponsorship"),
        )
        self.assertEqual(
            result[0]["choices"][4],
            ("F", "Female"),
        )
        self.assertEqual(
            result[0]["choices"][5],
            (u"à", u"à choice"),
        )

    def test_missing_name(self):
        text = """
        [field]
        max_length: 100
        """

        with self.assertRaisesRegexp(
            ValueError, "Field must include name attribute",
        ):
            parse(text)

    def test_missing_max_length(self):
        text = """
        [field]
        name: full_name
        error: Please enter your name
        """

        with self.assertRaisesRegexp(
            ValueError, "Field full_name must specify max_length",
        ):
            parse(text)


if __name__ == "__main__":
    unittest.main()
