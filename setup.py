from setuptools import setup, find_packages

DESCRIPTION = """
Create simple Django forms with a mini-language in your templates.

See:

https://github.com/prestontimmons/django-dslforms
"""


setup(
    name="django-dslforms",
    version="0.9.0",
    author="Preston Timmons",
    author_email="prestontimmons@gmail.com",
    url="https://github.com/prestontimmons/django-dslforms",
    description="Create simple Django forms with a mini-language in your templates.",
    long_description=DESCRIPTION,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "pyparsing==1.5.7",
    ],
)
