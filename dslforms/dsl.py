import unittest

from pyparsing import (
    alphanums,
    commaSeparatedList,
    Group,
    LineEnd,
    Literal,
    OneOrMore,
    ParseException,
    printables,
    restOfLine,
    Suppress,
    Word,
)


NL = Suppress(LineEnd())
LBRACKET = Suppress("[")
RBRACKET = Suppress("]")
COLON = Suppress(":")
RL = restOfLine
DASH = Suppress("-")
PIPE = Suppress("|")


def flatten(result):
    fields = []
    for entry in result:
        d = dict(entry[1:])

        if not d.get("name"):
            raise ParseException("Field must include name attribute")

        if d.get("widget", "charfield") in ["charfield", "textarea"]:
            if not d.get("max_length"):
                raise ParseException("Field must specify max_length")

        fields.append(dict(entry[1:]))
    return fields


def clean_attribute(tokens):
    key, value = tokens[0]

    if key == "max_length":
        return key, int(value)

    if key == "required":
        if value.lower().strip() == "false":
            return key, False
        return key, True

    return key, value.strip()


def parse(input_string):
    """
    Parses a form DSL in the following format:

        [field]
        name: category
        required: True
        choices: |
            - , -- Please Choose --
            - Sponsorship
            - My Account
            - M, Male
            - F, female
        widget: select
    """

    word = Word(alphanums + "_")

    header = LBRACKET + Literal("field") + RBRACKET + NL

    key = word("key")
    value = RL
    attribute = Group(key + COLON + ~PIPE + value)

    attribute.setParseAction(clean_attribute)
    choices = choice_parser()

    field = Group(header + 
        OneOrMore(attribute | choices)("attributes")
    )

    parser = OneOrMore(field).setParseAction(flatten)

    return parser.parseString(input_string)


def clean_choice(tokens):
    cleaned = []
    tlist = tokens.choices.asList()
    key = tlist[0]

    for choice in tlist[1:]:
        if len(choice) == 1:
            cleaned.append((choice[0], choice[0]))
        else:
            cleaned.append((choice[0], choice[1]))

    return [[key, cleaned]]


def choice_parser():
    word = Word(alphanums + "_")

    choice_start = word("key") + COLON + PIPE
    choice_options = Group(DASH + commaSeparatedList(printables + " "))
    choices = Group(choice_start + OneOrMore(choice_options))("choices")
    choices.setParseAction(clean_choice)

    return choices


class ChoiceParserTest(unittest.TestCase):

    def test_choices(self):
        parser = choice_parser()
        result = parser.parseString("""
            choices: |
              - one
              - two
              - , - Please Choose -
              - M, Male
              - F, Female
        """)

        self.assertEqual(result.asList(),
            [["choices", [('one', 'one'), ('two', 'two'), ('', '- Please Choose -'), ('M', 'Male'), ('F', 'Female')]]]
        )

    def test_missing_pipe(self):
        parser = choice_parser()
        
        with self.assertRaisesRegexp(ParseException, 'Expected "|"'):
            parser.parseString("""
                choices:
                  - one
                  - two
                  - , - Please Choose -
                  - M, Male
                  - F, Female
            """)


class FormParserTest(unittest.TestCase):

    def test_parser(self):
        text = """
        [field]
        name: full_name
        max_length: 100
        error: Please enter your name
        """

        result = parse(text)
        self.assertEqual(result[0]["name"], "full_name")
        self.assertEqual(result[0]["max_length"], 100)
        self.assertEqual(result[0]["error"], "Please enter your name")

    def test_required(self):
        text = """
        [field]
        name: city
        max_length: 80
        required: False
        testing: testing
        """

        result = parse(text)
        self.assertEqual(result[0]["name"], "city")
        self.assertEqual(result[0]["max_length"], 80)
        self.assertEqual(result[0]["required"], False)
        self.assertEqual(result[0]["testing"], "testing")

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
            - F, female
        widget: select
        """

        result = parse(text)
        self.assertEqual(result[0]["name"], "category")
        self.assertEqual(result[0]["required"], True)
        self.assertEqual(result[0]["widget"], "select")
        self.assertEqual(result[0]["choices"][0],
            ("", "-- Please Choose --"))

    def test_missing_name(self):
        text = """
        [field]
        max_length: 100
        """

        with self.assertRaisesRegexp(ParseException,
                "Field must include name attribute"):
            parse(text)

    def test_missing_max_length(self):
        text = """
        [field]
        name: full_name
        error: Please enter your name
        """

        with self.assertRaisesRegexp(ParseException,
                "Field must specify max_length"):
            parse(text)


if __name__ == "__main__":
    unittest.main()
