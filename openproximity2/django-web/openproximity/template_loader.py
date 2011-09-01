from django.template.loaders.app_directories import Loader

class ReversedLoader(Loader):
    def get_template_sources(self, template_name, template_dirs=None):
        vals = list(
            Loader.get_template_sources(self, template_name, template_dirs)
        )
        vals.reverse()
        return vals
