from django.contrib.staticfiles.management.commands.collectstatic import (
    Command as CollectStaticCommand,
)


class Command(CollectStaticCommand):
    def set_options(self, *args, **options):
        return_value = super().set_options(*args, **options)
        self.ignore_patterns += [
            "js/*.mjs",
            "js/modules/*",
            "js/plugins/*",
            "js/workers/*",
        ]
        return return_value
