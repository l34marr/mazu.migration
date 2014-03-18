import tempfile

from zope.annotation import IAnnotations

from Products.Five.browser import BrowserView

from collective.transmogrifier.transmogrifier import Transmogrifier
from collective.transmogrifier.transmogrifier import configuration_registry

from mazu.migration import logger

ANNOKEY = 'mazu.migration.config'
MIGRATION_CONFIG = 'mazu.migration'
PERSISTENT_CONFIG = 'persistent-mazu-config'


class MazuMigrationConfigView(BrowserView):
    """ View for setting persistent pipeline config.
    """

    def __init__(self, context, request):
        super(MazuMigrationConfigView, self).__init__(context, request)
        self.anno = IAnnotations(context)
        self.status = None

    def __call__(self):
        action = self.request.form.get('action')
        if action is not None:
            stat = []
            config = self.request.form['config'].strip()
            key = ANNOKEY
            oldconfig = self.getConfig()
            if config and self._configChanged(oldconfig, config):
                self.anno[key] = config
                stat.append('updated cofnig')
            elif not config and key in self.anno:
                del self.anno[key]
                stat.append('removed config')
            if stat:
                self.status = 'Changes: %s configuration.' % ' and '.join(stat)
            else:
                self.status = 'No changes'

        return self.index()

    def getConfig(self):
        if ANNOKEY in self.anno:
            return self.anno[ANNOKEY]
        else:
            get_conf = configuration_registry.getConfiguration
            fname = get_conf(MIGRATION_CONFIG)['configuration']
            return file(fname).read()

    def _configChanged(self, old, new):
        """ Compare configs with normalization of line endings.
        """
        if old == new:
            return False
        if old == new.replace('\r\n', '\n'):
            return False
        if old.strip() == new.replace('\r\n', '\n'):
            return False
        return True

    def isDefault(self):
        return ANNOKEY not in self.anno


CONFIGFILE = None


class MazuMigrationRunView(BrowserView):
    """ Run migration. """

    def registerPersistentConfig(self):
        global CONFIGFILE
        site = self.context
        anno = IAnnotations(site)
        config = ANNOKEY in anno and anno[ANNOKEY] or None

        # unregister old config
        if PERSISTENT_CONFIG in configuration_registry._config_ids:
            configuration_registry._config_ids.remove(PERSISTENT_CONFIG)
            del configuration_registry._config_info[PERSISTENT_CONFIG]

        # register new
        if config is not None:
            title = description = u'Persistent %s pipeline'
            tf = tempfile.NamedTemporaryFile('w+t', suffix='.cfg')
            tf.write(config)
            tf.seek(0)
            CONFIGFILE = tf
            configuration_registry.registerConfiguration(PERSISTENT_CONFIG,
                                                         title, description,
                                                         tf.name)
            return PERSISTENT_CONFIG
        else:
            return None

    def __call__(self):

        logger.info("Start importing.")
        config = self.registerPersistentConfig() or MIGRATION_CONFIG
        Transmogrifier(self.context)(config)
        logger.info("Stop importing.")
        return "Migration finished."
