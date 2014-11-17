from fabric.api import env
import yaml

from .provisioning import *  # NOQA
from .deploy import *  # NOQA
from .utils import *  # NOQA
from .environments import *  # NOQA


if os.path.isfile('env.yml'):
    with open('env.yml') as env_settings_file:
        env_settings = yaml.load(env_settings_file.read())

        # Using setdefault rather than update, as to avoid overriding
        for key, value in env_settings.iteritems():
            setattr(env, key, value)
