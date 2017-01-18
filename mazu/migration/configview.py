import tempfile

from zope.annotation import IAnnotations

from Products.Five.browser import BrowserView

from collective.transmogrifier.transmogrifier import Transmogrifier
from collective.transmogrifier.transmogrifier import configuration_registry

from mazu.migration import logger

import ConfigParser
import io

ANNOKEY = 'mazu.migration.config'
MIGRATION_CONFIG = 'mazu.migration'
PERSISTENT_CONFIG = 'persistent-mazu-config'
EXT_PARAM_CONFIG = 'ext-param-mazu-config'
EXT_PARAM_CONFIG_FILE = 'ext-param-mazu-config-tmpfile.tmp'


class MazuMigrationConfigView(BrowserView):
    """ View for setting persistent pipeline config.
    """

    def __init__(self, context, request):
        super(MazuMigrationConfigView, self).__init__(context, request)
        self.anno = IAnnotations(context)
        self.status = None

    def __call__(self):
        action = self.request.form.get('action')
        #import pdb; pdb.set_trace()
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
            tf = tempfile.NamedTemporaryFile('w+t', suffix='.cfg', dir='/tmp')
            tf.write(config)
            tf.seek(0)
            CONFIGFILE = tf
            configuration_registry.registerConfiguration(PERSISTENT_CONFIG,
                                                         title, description,
                                                         tf.name)
            return PERSISTENT_CONFIG
        else:
            return None

    def getDefaultConfig(self):
        get_conf = configuration_registry.getConfiguration
        fname = get_conf(MIGRATION_CONFIG)['configuration']
        return file(fname).read()

    def registerConfigExtParam(self):

        defconfig = self.getDefaultConfig()


        config = ConfigParser.RawConfigParser(allow_no_value=True)
        config.readfp(io.BytesIO(defconfig))

        # unregister old config
        if EXT_PARAM_CONFIG in configuration_registry._config_ids:
            configuration_registry._config_ids.remove(EXT_PARAM_CONFIG)
            del configuration_registry._config_info[EXT_PARAM_CONFIG]


        if config is not None:
            dest_catalog_path = self.request.get('dest_catalog_path')
            dest_path_value = "python:item['_path'].replace('/temple',%s)"%dest_catalog_path

            config.set('catalogsource', 'remote-url', self.request.get('remote-url'))
            config.set('catalogsource', 'remote-username', self.request.get('remote-username'))
            config.set('catalogsource', 'remote-password', self.request.get('remote-password'))
            config.set('catalogsource', 'catalog-path', self.request.get('catalog-path'))
            config.set('catalogsource', 'catalog-query', self.request.get('catalog-query'))
            config.set('inserter', 'value', dest_path_value)

            title = description = u'Persistent %s pipeline'
            #tf = tempfile.NamedTemporaryFile('w+t', suffix='.cfg', dir='/tmp',  delete=False)
            file_path = '/tmp/%s'%EXT_PARAM_CONFIG_FILE
            tf = open(file_path, 'w+t')
            config.write(tf)
            tf.seek(0)
            configuration_registry.registerConfiguration(EXT_PARAM_CONFIG,
                                                         title, description,
                                                         tf.name)
            return EXT_PARAM_CONFIG
        else:
            return None


    def __call__(self):

        logger.info("Start importing.")

        if self.request.get('remote-url'):
            config = self.registerConfigExtParam()
        else:
            config = self.registerPersistentConfig() or MIGRATION_CONFIG
        try:
            Transmogrifier(self.context)(config)
            logger.info("Finish importing.")
            result = 'ok'
        except Exception as err:
            logger.error("Import Error: %s"%err)
            result = err
        return result
