import os
import posixpath
import re
from urllib.parse import unquote
from urllib.parse import urldefrag
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.staticfiles.storage import HashedFilesMixin
from django.contrib.staticfiles.storage import (
    ManifestStaticFilesStorage as DefaultManifestStaticFilesStorage,
)


def add_js_static_pattern(pattern):
    if pattern[0] == "*.js":
        templates = pattern[1] + (
            (
                "(?P<matched>staticUrl\\(['\"]{0,1}\\s*(?P<url>.*?)[\"']{0,1}\\))",
                "'%(url)s'",
            )
        )
        pattern = (pattern[0], templates)
    return pattern


class ManifestStaticFilesStorage(DefaultManifestStaticFilesStorage):
    patterns = tuple(map(add_js_static_pattern, HashedFilesMixin.patterns))

    def url_converter(self, name, hashed_files, template=None):
        """
        Return the custom URL converter for the given file name.
        """
        # Modified from
        # https://github.com/django/django/blob/main/django/contrib/staticfiles/storage.py
        # to handle absolute URLS

        if template is None:
            template = self.default_template

        def converter(matchobj):
            """
            Convert the matched URL to a normalized and hashed URL.
            This requires figuring out which files the matched URL resolves
            to and calling the url() method of the storage.
            """
            matches = matchobj.groupdict()
            matched = matches["matched"]
            url = matches["url"]

            # Ignore absolute/protocol-relative and data-uri URLs.
            if re.match(r"^[a-z]+:", url):
                return matched

            # Strip off the fragment so a path-like fragment won't interfere.
            url_path, fragment = urldefrag(url)

            # Ignore URLs without a path
            if not url_path:
                return matched

            if url_path.startswith("/"):
                # Absolute paths are assumed to have their root at STATIC_ROOT
                target_name = url_path[1:]
            else:
                # We're using the posixpath module to mix paths and URLs conveniently.
                source_name = name if os.sep == "/" else name.replace(os.sep, "/")
                target_name = posixpath.join(posixpath.dirname(source_name), url_path)

            # Determine the hashed name of the target file with the storage backend.
            hashed_url = self._url(
                self._stored_name,
                unquote(target_name),
                force=True,
                hashed_files=hashed_files,
            )

            transformed_url = "/".join(
                url_path.split("/")[:-1] + hashed_url.split("/")[-1:],
            )

            # Restore the fragment that was stripped off earlier.
            if fragment:
                transformed_url += ("?#" if "?#" in url else "#") + fragment

            if url_path.startswith("/"):
                transformed_url = urljoin(settings.STATIC_URL, transformed_url[1:])

            # Return the hashed version to the file
            matches["url"] = unquote(transformed_url)
            return template % matches

        return converter
