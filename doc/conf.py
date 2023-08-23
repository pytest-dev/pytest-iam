#!/usr/bin/env python3
import datetime
import os
import sys
from importlib import metadata

sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../pytest_iam"))

# -- General configuration ------------------------------------------------


extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.graphviz",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_issues",
    "myst_parser",
]

templates_path = ["_templates"]

source_suffix = [".rst", ".md"]
master_doc = "index"
project = "pytest_iam"
year = datetime.datetime.now().strftime("%Y")
copyright = f"{year}, Yaal Coop"
author = "Yaal Coop"

release = metadata.version("pytest_iam")
version = "%s.%s" % tuple(map(int, release.split(".")[:2]))
language = "en"
exclude_patterns = []
pygments_style = "sphinx"
todo_include_todos = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "canaille": ("https://canaille.readthedocs.io/en/latest/", None),
    "flask": ("https://flask.palletsprojects.com/en/latest/", None),
    "authlib": ("https://docs.authlib.org/en/latest/", None),
}

issues_uri = "https://gitlab.com/yaal/pytest_iam/-/issues/{issue}"
issues_pr_uri = "https://gitlab.com/yaal/pytest_iam/-/merge_requests/{pr}"
issues_commit_uri = "https://gitlab.com/yaal/pytest_iam/-/commit/{commit}"

# -- Options for HTML output ----------------------------------------------

html_theme = "alabaster"
html_static_path = []


# -- Options for HTMLHelp output ------------------------------------------

htmlhelp_basename = "pytest_iamdoc"
# html_logo = ""


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {}
latex_documents = [
    (master_doc, "pytest_iam.tex", "pytest_iam documentation", "Yaal Coop", "manual")
]

# -- Options for manual page output ---------------------------------------

man_pages = [(master_doc, "pytest_iam", "pytest_iam Documentation", [author], 1)]

# -- Options for Texinfo output -------------------------------------------

texinfo_documents = [
    (
        master_doc,
        "pytest_iam",
        "pytest_iam documentation",
        author,
        "pytest_iam",
        "One line description of project.",
        "Miscellaneous",
    )
]
