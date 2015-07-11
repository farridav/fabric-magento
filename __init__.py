from fabric.api import env
import yaml

from .provisioning import *  # NOQA
from .deploy import *  # NOQA
from .utils import *  # NOQA
from .environments import *  # NOQA

# Set the root for forming absolute paths
env.root = os.path.dirname(os.path.dirname(__file__))

if os.path.isfile(os.path.join(env.root, 'env.yml')):
    with open(os.path.join(env.root, 'env.yml')) as env_settings_file:
        env_settings = yaml.load(env_settings_file.read())

        # Using setdefault rather than update, as to avoid overriding
        for key, value in env_settings.iteritems():
            setattr(env, key, value)
