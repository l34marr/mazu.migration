from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Expression, Condition
import ast

class MazuFieldMapSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous

        self.keys_map = options.get('keys_map', None)

    def __iter__(self):
        if self.keys_map:
            keys_map = ast.literal_eval(self.keys_map)
            for item in self.previous:
                for key_map in keys_map:
                    new_value = item.get(key_map, None)
                    if new_value:
                        new_key = keys_map[key_map]
                        item[new_key] = new_value
                yield item
