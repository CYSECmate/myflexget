from __future__ import unicode_literals, division, absolute_import
from builtins import * 

import putiopy
import logging

from flexget import plugin
from flexget.event import event
from flexget.utils.template import RenderError

log = logging.getLogger('putio')


class OutputPutio(object):
    """
    Example:
      putio:
        token: <TOKEN> (default: (none))
        clean_completed: <CLEAN_COMPLETED> (default: (yes))
        root_dir_id: <PARENT_ID> (default: (0))
    """
    schema = {
        'anyOf': [
            {'type': 'boolean'},
            {
                'type': 'object',
                'properties': {
                    'token': {'type': 'string'},
                    'clean_completed': {'type': 'boolean'},
                    'root_dir_id': {'type': 'string'}
                },
                'additionalProperties': False
            }
        ]
    }
  

    def add_torrent_url(self, client, torrent_url, dir_id):
        """ Adds a new transfer. """
        transfer = client.Transfer.add_url(torrent_url, dir_id)
        log.info('Added torrent %s to %s folder', torrent_url, dir_id)


    def get_directory_id(self, client, form_data, config):
        """ Get directory id of destination directory. """
        dir_is_present = False
        files = client.File.list(config.get("root_dir_id"))
        for i in files:
            if i.name == form_data.get("dir"):
                dir_id = i.id
                dir_is_present = True
                continue
        if dir_is_present == False:
    	    dir_id = 0
        return dir_id


    def create_folder(self, client, form_data, config):
        """ Create folder. """
        folder = client.File.create_folder(form_data.get("dir"), config.get("root_dir_id"))
        log.info('Folder %s created into putio', form_data.get("dir"))

    
    def clean_completed(self, client):
        """ Clean completed transfers. """
        clean = client.Transfer.clean()
        log.info('Completed transfer cleaned')


    def prepare_config(self, config):
        """ Set default config values. """
        if isinstance(config, bool):
            config = {'enabled': config}
        config.setdefault('enabled', True)
        config.setdefault('root_dir_id', 0)
        config.setdefault('clean_completed', True)
        return config


    def add_entries(self, task, config):
        """ Main function. """
        client = putiopy.Client(config.get("token"))
        for entry in task.accepted:
            form_data = {}
	    if entry.get('dir'):
	        form_data['dir'] = entry.render(entry['dir'])
                dir_id = self.get_directory_id(client, form_data, config)
                if dir_id == 0:
	            self.create_folder(client, form_data, config)
                    dir_id = self.get_directory_id(client, form_data, config)
                log.info("Destination directory is %s", form_data.get("dir"))
            else:
   	        dir_id = config.get("root_dir_id")
  	
	    log.info("Destination directory ID is %s", dir_id)

            """ Adds a new transfer. """
            self.add_torrent_url(client, entry['url'], dir_id)
	    
            """ Clean completed transfer. """
            if config.get('clean_completed'):
                self.clean_completed(client)

    def on_task_output(self, task, config):
        """Add torrents to putio at exit."""
        if task.accepted:
            config = self.prepare_config(config)
            self.add_entries(task, config)


@event('plugin.register')
def register_plugin():
    plugin.register(OutputPutio, 'putio', api_ver=2)

