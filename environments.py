from fabric.api import env, task, execute, puts
from fabric.context_managers import quiet
from fabric.colors import green
from fabric.decorators import with_settings
from fabric.operations import run


@task
def use(name=''):
    """
    Use the Given environment, if no environment is passed,
    list off available environments
    """
    if not name or name not in env.environments:
        puts(green('Available Environments: \n'))
        for environment in env.environments:
            puts('\t' + green(environment))
    else:
        env.environment = env.environments.get(name)
        env.name = name
        env.user = env.environment['user']
        env.hosts = env.environment['hosts']
        env.playbook = env.environment['playbook']
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
        app_persistent_dirs # The folders that persisten between deploys

    """

    with quiet():
        env_vars = run('printenv | grep {}'.format(prefix))

    env_vars_list = env_vars.split()
    for var in env_vars_list:
        key, value = var.split('=')
        key = key.replace(prefix, '')
        key = key.lower()
        env[key] = value
