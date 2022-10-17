import re
from urllib.parse import quote
from urllib.parse import urljoin

from django import template
from django.apps import apps
from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
from django.templatetags.static import PrefixNode
from django.templatetags.static import StaticNode

from npm_mjs.tools import get_last_run

register = template.Library()


class StaticTranspileNode(StaticNode):
    @classmethod
    def handle_simple(cls, path):
        path = re.sub(r"^js/(.*)\.mjs", r"js/\1.js", path)
        if apps.is_installed("django.contrib.staticfiles"):
            from django.contrib.staticfiles.storage import staticfiles_storage

            if isinstance(staticfiles_storage, ManifestStaticFilesStorage):
                return staticfiles_storage.url(path)
            else:
                return staticfiles_storage.url(path) + "?v=%s" % get_last_run(
                    "transpile",
                )
        else:
            return urljoin(
                PrefixNode.handle_simple("STATIC_URL"),
                quote(path),
            ) + "?v=%s" % get_last_run("transpile")


@register.tag
def static(parser, token):
    """
    Join the given path with the STATIC_URL setting adding a version number
    and the location of the transpile folder.
    Usage::
        {% static path [as varname] %}
    Examples::
        {% static "js/index.mjs" %} # turns into js/index.js?v=213...
        {% static "css/style.css" %} # turns into css/style.css?v=213...
        {% static variable_with_path %}
        {% static variable_with_path as varname %}
    """
    return StaticTranspileNode.handle_token(parser, token)
