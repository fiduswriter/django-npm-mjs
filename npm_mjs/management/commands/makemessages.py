from base.management import BaseCommand
from django.core.management.commands import makemessages

# This makes makemessages create both translations for Python and JavaScript
# code in one go.

# Note that translating JavaScript files with template strings requires xgettext 0.24 (see README.md))


class Command(makemessages.Command, BaseCommand):

    def add_arguments(self, parser):
        # Call the parent class's add_arguments first
        super().add_arguments(parser)

        # Modify the domain argument's help text
        for action in parser._actions:
            if action.dest == "domain":
                action.help = (
                    "Domain of the messages file ('django' or 'djangojs'). "
                    "By default, both domains will be processed."
                )
                action.default = None  # This indicates we'll handle both domains
            elif action.dest == "locale":
                action.help = "Locale(s) to process. If none are specified, all locales will be processed."
            elif action.dest == "all":
                action.help = (
                    "Process all locales. "
                    "If not specified, and no locales are provided, all locales will be processed."
                )
                action.default = False

    def handle(self, *args, **options):
        options["ignore_patterns"] += [
            "venv",
            ".direnv",
            "node_modules",
            "static-transpile",
        ]
        if len(options["locale"]) == 0 and not options["all"]:
            options["all"] = True
        if options["domain"]:
            self.stdout.write("Domain %s" % options["domain"])
            return super().handle(*args, **options)
        else:
            options["domain"] = "django"
            self.stdout.write("Domain %s" % options["domain"])
            super().handle(*args, **options)
            options["domain"] = "djangojs"
            self.stdout.write("Domain %s" % options["domain"])
            super().handle(*args, **options)
