import base64
from zope.interface import implements
from zope.interface import classProvides
from zope.schema import getFieldsInOrder
from zope.component import queryMultiAdapter, getMultiAdapter
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

from plone.namedfile.interfaces import INamedField
from plone.dexterity.utils import iterSchemata
from z3c.form.interfaces import IDataManager, NO_VALUE, IValue


from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from transmogrify.dexterity.interfaces import IDeserializer


_marker = object()


class MazuDataFields(object):
    """
    """

    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context
        self.datafield_prefix = options.get('datafield-prefix', '_datafield_')
        self.root_path_length = len(self.context.getPhysicalPath())

    def __iter__(self):
        for item in self.previous:
            if '_path' not in item:
                yield item
                continue

            obj = self.context.unrestrictedTraverse(item['_path'].lstrip('/'),
                                                    None)

            if obj is None:
                yield item
                continue

            # do nothing if we got a wrong object through acquisition
            path = item['_path']
            if path.startswith('/'):
                path = path[1:]
            if '/'.join(obj.getPhysicalPath()[self.root_path_length:]) != path:
                yield item
                continue

            for schemata in iterSchemata(obj):
                for name, field in getFieldsInOrder(schemata):
                    if field.readonly:
                        continue
                    if INamedField.providedBy(field):
                       value = item.get('%s%s' % (self.datafield_prefix, name),
                                        _marker)
                       if value is not _marker:
                          deserializer = IDeserializer(field)

                          # prepare value data and content type
                          value['data'] = base64.b64decode(value['data'])
                          value['contenttype'] = value['content_type']
                          value = deserializer(value, None, item)
                          field.set(field.interface(obj), value)

                    # Get the widget's current value, if it has one then leave
                    # it alone
                    value = getMultiAdapter(
                        (obj, field), IDataManager).query()
                    if not(value is field.missing_value
                           or value is NO_VALUE):
                        continue

                    # Finally, set a default value if nothing is set so far
                    default = queryMultiAdapter((
                        obj,
                        obj.REQUEST,  # request
                        None,  # form
                        field,
                        None,  # Widget
                    ), IValue, name='default')
                    if default is not None:
                        default = default.get()
                    if default is None:
                        default = getattr(field, 'default', None)
                    if default is None:
                        try:
                            default = field.missing_value
                        except AttributeError:
                            pass
                    field.set(field.interface(obj), default)

            notify(ObjectModifiedEvent(obj))
            yield item
