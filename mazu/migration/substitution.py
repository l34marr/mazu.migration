import re

from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection

class SubstitutionSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.key = options['key'].strip()
        self.ckey = options.get('condition_key', '').strip()
        self.cvalue = options.get('condition_value', '').strip()
        self.oldkey = "_old" + self.key
        self.options = options
        self.previous = previous

    def __iter__(self):
        key = self.key
        for item in self.previous:
            if not item['_type'] in ('Temple', 'Photo'):
                continue
            if key in item:
                old = item[key]
                for option in self.options:
                    if re.compile(option).match(item[key]):
                        new = self.options.get(option)
                        if item['_type'] == 'Photo':
                            new = '%s/%s' % (new, old.split('/')[-2])

                        if key == '_path':
                            new = '%s/%s' % (new, item['id'])

                        if new is not None and old != new:
                            item[key] = new.strip()
                            item[self.oldkey] = old
            yield item
