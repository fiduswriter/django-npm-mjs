import re

from django.utils.six.moves.urllib.parse import quote, urljoin
from django import template
from django.templatetags.static import StaticNode, PrefixNode
from django.apps import apps

from npm_mjs.management.commands.transpile import LAST_RUN

register = template.Library()


class StaticTranspileNode(StaticNode):

    @classmethod
    def handle_simple(cls, path):
        path = re.sub(
            r'^js/(.*)\.mjs',
            r'js/transpile/\1.js',
            path
        )
        if apps.is_installed('django.contrib.staticfiles'):
            from django.contrib.staticfiles.storage import staticfiles_storage
            return (
                staticfiles_storage.url(path) +
                '?v=%s' % LAST_RUN['version']
            )
        else:
            return (
                urljoin(
                    PrefixNode.handle_simple("STATIC_URL"),
                    quote(path)
                ) + '?v=%s' % LAST_RUN['version']
            )


@register.tag
def static(parser, token):
    """
    Join the given path with the STATIC_URL setting adding a version number
    and the location of the transpile folder.
    Usage::
        {% static path [as varname] %}
    Examples::
        {% static "js/index.mjs" %} # turns into js/transpile/index.js?v=213...
        {% static "css/style.css" %} # turns into css/style.css?v=213...
        {% static variable_with_path %}
        {% static variable_with_path as varname %}
    """
    return StaticTranspileNode.handle_token(parser, token)


@register.inclusion_tag('npm_mjs/static_urls_js.html')
def static_urls_js():
    """
    Add global variables to JavaScript about the location and latest version of
    transpiled files.
    Usage::
        {% static_urls_js %}
    """
    if apps.is_installed('django.contrib.staticfiles'):
        from django.contrib.staticfiles.storage import staticfiles_storage
        static_base_url = staticfiles_storage.base_url
    else:
        static_base_url = PrefixNode.handle_simple("STATIC_URL")
    transpile_base_url = urljoin(static_base_url, 'js/transpile/')
    return {
        'static_base_url': static_base_url,
        'transpile_base_url': transpile_base_url,
        'version': LAST_RUN['version']
    }
