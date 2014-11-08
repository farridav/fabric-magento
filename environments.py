from fabric.api import env, task, execute
from fabric.context_managers import quiet
from fabric.decorators import with_settings
from fabric.operations import run


@task
def vagrant():
    """
    Use the Vagrant environment
    """
    environment = env.environments['vagrant']
    env.user = environment['user']
    env.hosts = environment['hosts']
    env.playbook = environment['playbook']
    execute(get_environment_variables)


@task
def stage():
    """
    Use the Stage environment
    """
    environment = env.environments['stage']
    env.user = environment['user']
    env.hosts = environment['hosts']
    env.playbook = environment['playbook']
    execute(get_environment_variables)


@task
def live():
    """
    Use the Live environment
    """
    environment = env.environments['live']
    env.user = environment['user']
    env.hosts = environment['hosts']
    env.playbook = environment['playbook']
    execute(get_environment_variables)


@with_settings(warn_only=True)
def get_environment_variables(prefix='APP_'):
    """
    Get bash environment variables and set variables required by fabric,
    gives us access to the following variables by putting them in fabrics `env`

        release_dir         # The location of our releases
        current_release     # The path to the current release
        previous_release    # The path to the previous release
        db_name             # The database name
        db_user             # The database user
        db_host             # The database host
        db_pass             # The database password
        mage_src            # The Location of Magento's source
        media_dir           # The Location of our media folder
        var_dir             # The Location of our var folder
        unix_user           # The applications user
        unix_group          # The applications group

    """

    with quiet():
        env_vars = run('printenv | grep {}'.format(prefix))

    env_vars_list = env_vars.split()
    for var in env_vars_list:
        key, value = var.split('=')
        key = key.replace(prefix, '')
        key = key.lower()
        env[key] = value
