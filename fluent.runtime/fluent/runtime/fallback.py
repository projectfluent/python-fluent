# -*- coding: utf-8 -*-

import codecs
import os
import six


class FluentLocalization(object):
    """
    Generic API for Fluent applications.

    This handles language fallback, bundle creation and string localization.
    It uses the given resource loader to load and parse Fluent data.
    """
    def __init__(
        self, locales, resource_ids, resource_loader,
        use_isolating=False,
        bundle_class=None, functions=None,
    ):
        self.locales = locales
        self.resource_ids = resource_ids
        self.resource_loader = resource_loader
        self.use_isolating = use_isolating
        if bundle_class is None:
            from fluent.runtime import FluentBundle
            self.bundle_class = FluentBundle
        else:
            self.bundle_class = bundle_class
        self.functions = functions
        self._bundle_cache = []
        self._bundle_it = self._iterate_bundles()

    def format_value(self, msg_id, args=None):
        for bundle in self._bundles():
            if not bundle.has_message(msg_id):
                continue
            msg = bundle.get_message(msg_id)
            if not msg.value:
                continue
            val, errors = bundle.format_pattern(msg.value, args)
            return val
        return msg_id

    def _create_bundle(self, locales):
        return self.bundle_class(
            locales, functions=self.functions, use_isolating=self.use_isolating
        )

    def _bundles(self):
        bundle_pointer = 0
        while True:
            if bundle_pointer == len(self._bundle_cache):
                try:
                    self._bundle_cache.append(next(self._bundle_it))
                except StopIteration:
                    return
            yield self._bundle_cache[bundle_pointer]
            bundle_pointer += 1

    def _iterate_bundles(self):
        for first_loc in range(0, len(self.locales)):
            locs = self.locales[first_loc:]
            for resources in self.resource_loader.resources(locs[0], self.resource_ids):
                bundle = self._create_bundle(locs)
                for resource in resources:
                    bundle.add_resource(resource)
                yield bundle


class AbstractResourceLoader(object):
    """
    Interface to implement for resource loaders.
    """
    def resources(self, locale, resource_ids):
        """
        Yield lists of FluentResource objects, corresponding to
        each of the resource_ids.
        If there are multiple locations, this may yield multiple lists.
        If a resource isn't found in any location, yield a partial list,
        but don't yield empty lists.
        """
        raise NotImplementedError


class FluentResourceLoader(AbstractResourceLoader):
    """
    Resource loader to read Fluent files from disk.

    Different locales are in different locations based on locale code.
    The locale code should be encoded as `{locale}` in the roots, or in
    the resource_ids.
    This loader does not support loading resources for one bundle from
    different roots.
    """
    def __init__(self, roots):
        """
        Create a resource loader. The roots may be a string for a single
        location on disk, or a list of strings.
        """
        self.roots = [roots] if isinstance(roots, six.text_type) else roots
        from fluent.runtime import FluentResource
        self.Resource = FluentResource

    def resources(self, locale, resource_ids):
        for root in self.roots:
            resources = []
            for resource_id in resource_ids:
                path = self.localize_path(os.path.join(root, resource_id), locale)
                if not os.path.isfile(path):
                    continue
                content = codecs.open(path, 'r', 'utf-8').read()
                resources.append(self.Resource(content))
            if resources:
                yield resources

    def localize_path(self, path, locale):
        return path.format(locale=locale)
