import base64
import urllib
import urllib2
import json as simplejson

from collective.jsonmigrator import catalogsource


class MazuCatalogSourceSection(catalogsource.CatalogSourceSection):
    """ Custom catalog source section.

    Implements additional 'include_subobjects' option. If this option is set to
    true then all subitems will be migrated as well.
    """

    def __init__(self, transmogrifier, name, options, previous):
        super(MazuCatalogSourceSection, self).__init__(transmogrifier, name,
                                                       options, previous)

        catalog_path = self.get_option('catalog-path', '/Plone/portal_catalog')
        self.include_subobjects = self.get_option('include_subobjects', False)

        if self.include_subobjects:
            for path in self.item_paths[:]:
                sub_query = base64.b64encode(
                    "{'path':{'query':'%s', 'depth':10}}" % path)
                url = '%s%s/get_catalog_results' % (self.remote_url,
                                                    catalog_path)
                req = urllib2.Request(url, urllib.urlencode(
                    {'catalog_query': sub_query}))
                try:
                    file_ = urllib2.urlopen(req)
                    resp = file_.read()
                except urllib2.URLError:
                    raise

                self.item_paths.extend(simplejson.loads(resp))
