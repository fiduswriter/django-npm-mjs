import os
import re
import shutil
import tempfile
import urllib

from base.management import BaseCommand
from django.core.management import call_command
from django.core.management.commands import makemessages
from django.core.management.utils import popen_wrapper
from django.utils.translation import templatize
from django.utils.functional import cached_property
from django.utils.jslex import JsLexer, Tok
JsLexer.both_before.append(Tok("template", r"`([^\\]|(\\(.|\n)))*?`", next="div"),)

# This makes makemessages create both translations for Python and JavaScript
# code in one go.
#
# Additionally, it works around xgettext not being able to work with ES2015
# template strings [1] by transpiling the JavaScript files in a special way to
# replace all template strings.
#
# [1] https://savannah.gnu.org/bugs/?50920


def prepare_js_for_gettext(js):
    """
    Convert the JavaScript source `js` into something resembling C for
    xgettext.
    What actually happens is that all the regex literals are replaced with
    "REGEX".
    """

    def escape_quotes(m):
        """Used in a regex to properly escape double quotes."""
        s = m[0]
        if s == '"':
            return r"\""
        else:
            return s

    lexer = JsLexer()
    c = []
    for name, tok in lexer.lex(js):
        if name == "regex":
            # C doesn't grok regexes, and they aren't needed for gettext,
            # so just output a string instead.
            tok = '"REGEX"'
        elif name == "string":
            # C doesn't have single-quoted strings, so make all strings
            # double-quoted.
            if tok.startswith("'"):
                guts = re.sub(r"\\.|.", escape_quotes, tok[1:-1])
                tok = '"' + guts + '"'
        elif name == "template":
            # Split the template string into chunks using the ${...} pattern
            chunks = re.findall(r'\${(.*?)}', tok)
            # Concatenate the chunks with "+"
            for chunk in chunks:
                tok = tok.replace('${' + chunk + '}', '" + ' + chunk + ' + "', 1)
            # Replace backtick-quotes with double-quotes.
            tok = '"' + tok[1:-1] +'"'
        elif name == "id":
            # C can't deal with Unicode escapes in identifiers.  We don't
            # need them for gettext anyway, so replace them with something
            # innocuous
            tok = tok.replace("\\", "U")
        c.append(tok)
    return "".join(c)


class BuildFile(makemessages.BuildFile):

    @cached_property
    def is_templatized(self):
        if self.domain == "djangojs":
            return True
        elif self.domain == "django":
            file_ext = os.path.splitext(self.translatable.file)[1]
            return file_ext != ".py"
        return False

    def preprocess(self):
        """
        Preprocess (if necessary) a translatable file before passing it to
        xgettext GNU gettext utility.
        """
        if not self.is_templatized:
            return
        with open(self.path, encoding="utf-8") as fp:
            src_data = fp.read()

        if self.domain == "djangojs":
            content = prepare_js_for_gettext(src_data)
        elif self.domain == "django":
            content = templatize(src_data, origin=self.path[2:])

        with open(self.work_path, "w", encoding="utf-8") as fp:
            fp.write(content)

    def cleanup(self):
        pass

class Command(makemessages.Command, BaseCommand):
    build_file_class = BuildFile

    def handle(self, *args, **options):
        #call_command("transpile")
        options["ignore_patterns"] += [
            "venv",
            ".direnv",
            "node_modules",
            "static-transpile",
        ]
        options["domain"] = "django"
        super().handle(*args, **options)
        options["domain"] = "djangojs"
        self.temp_dir_out = tempfile.mkdtemp()
        self.temp_dir_in = tempfile.mkdtemp()
        super().handle(*args, **options)
        shutil.rmtree(self.temp_dir_in)
        shutil.rmtree(self.temp_dir_out)

    # def process_locale_dir(self, locale_dir, files):
    #     if self.domain == "djangojs":
    #         for file in files:
    #             # We need to copy the JS files first, as otherwise babel will
    #             # attempt to read package.json files in subdirs, such as
    #             # base/package.json
    #             in_path = urllib.parse.urljoin(self.temp_dir_in + "/", file.dirpath)
    #             os.makedirs(in_path, exist_ok=True)
    #             in_file = urllib.parse.urljoin(in_path + "/", file.file)
    #             shutil.copy2(file.path, in_file)
    #             out_path = urllib.parse.urljoin(self.temp_dir_out + "/", file.dirpath)
    #             file.dirpath = out_path
    #         os.chdir(".transpile/")
    #         out, err, status = popen_wrapper(
    #             [
    #                 "npm",
    #                 "run",
    #                 "babel-transform-template-literals",
    #                 "--",
    #                 "--out-dir",
    #                 self.temp_dir_out,
    #                 self.temp_dir_in,
    #             ],
    #         )
    #         os.chdir("../")
    #
    #     super().process_locale_dir(locale_dir, files)
    #
    # def write_po_file(self, potfile, locale):
    #     if self.domain == "djangojs":
    #         with open(potfile, encoding="utf-8") as fp:
    #             msgs = fp.read()
    #         # Remove temp dir path info
    #         msgs = msgs.replace(self.temp_dir_out + "/", "")
    #         with open(potfile, "w", encoding="utf-8") as fp:
    #             fp.write(msgs)
    #     super().write_po_file(potfile, locale)
