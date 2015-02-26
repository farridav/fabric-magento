import os

from fabric.api import task, puts, local, env, cd, lcd
from fabric.operations import run, put, open_shell, sudo, get, abort
from fabric.colors import green, red


@task
def clear_cache():
    """
    Manually delete the session and cache files
    """
    sudo('rm -rf {}/var/session/*'.format(env.current_release))
    sudo('rm -rf {}/var/cache/*'.format(env.current_release))


@task
def restart_server():
    """
    Reload the server, ...may currently be overkill
    """
    sudo('service php5-fpm restart')
    sudo('service nginx restart')
    sudo('service varnish restart')


@task
def shell():
    """
    Open an interactive shell
    """
    open_shell()


@task
def dbshell():
    """
    Open an mysql shell
    """
    db_kwargs = {
        'user': env.db_user,
        'pass': env.db_pass,
        'database': env.db_name,
        'host': env.db_host
    }
    run('mysql -u{user} -p\'{pass}\' -h{host} {database}'.format(**db_kwargs))


@task
def put_media():
    """
    Put media to local to the given environment, then ensure permissions are
    set correctly
    """

    exclude = ['import', 'cache', 'css_secure', 'css', 'js']
    exclusions = ''
    for exclusion in exclude:
        exclusions += ' --exclude ' + exclusion

    if env.environment == 'live':
        abort(red('Cannot put media to a live environment!'))

    local('rsync -avz {} site/media/ {}@{}:{}'.format(
          exclusions, env.user, env.host, env.media_dir))
    sudo('chown -R {}:www-data {}'.format(env.unix_user, env.media_dir))
    sudo('chmod -R 775 {}'.format(env.media_dir))


@task
def get_media():
    """
    Copy media from the given environment to local
    """
    exclude = ['import', 'cache', 'css_secure', 'css', 'js']
    exclusions = ''
    for exclusion in exclude:
        exclusions += ' --exclude ' + exclusion
    local('rsync -avz {} {}@{}:{}/ site/media/'.format(
        exclusions, env.user, env.host, env.media_dir))


@task
def get_db():
    db_kwargs = {
        'user': env.db_user,
        'pass': env.db_pass,
        'database': env.db_name,
        'host': env.db_host,
        'dbdump': os.path.join(env.release_dir, 'current.sql.gz'),
    }
    run('mysqldump -u{user} -p\'{pass}\' -h{host} {database} | gzip'
        ' > {dbdump}'.format(**db_kwargs))

    get(db_kwargs['dbdump'], os.getcwd())


@task
def put_db():
    if env.name == 'live':
        abort(red('Cannot put db to a live environment!'))
    with lcd(env.root):
        put('current.sql.gz', env.release_dir)
    run('gzip -d {}'.format(os.path.join(env.release_dir, 'current.sql.gz')))
    db_kwargs = {
        'user': env.db_user,
        'pass': env.db_pass,
        'database': env.db_name,
        'host': env.db_host,
        'dbdump': os.path.join(env.release_dir, 'current.sql'),
    }
    run('mysql -u{user} -p\'{pass}\' -h{host} {database} -e "drop database '
        '{database}; create database {database}"'.format(**db_kwargs))

    run('mysql -u{user} -p\'{pass}\' -h{host} {database} < {dbdump}'.format(
        **db_kwargs))

    run('rm {}'.format(db_kwargs['dbdump']))


@task
def develop():
    """
    Use this to sync your local files with the files on remote, it runs once
    every second
    """
    print(green('Pushing local changes'))
    local('watch -n1 rsync -avz --exclude media site/ {}@{}:{}/'.format(
          env.user, env.host, env.current_release))


@task
def update_magento_core():
    """
    Update the Magento src dir to use the latest files

    (Affects all future deploys)
    """
    _mage_module('Mage_All_Latest', env.mage_src, action='install', force=True)
    puts(green('Core updated, this will affect all future deploys...'))


@task
def uninstall_module(module, force=False):
    """
    UnInstall a given module
    """
    _mage_module(module, env.current_release, action='uninstall', force=force)


@task
def install_module(module, force=False):
    """
    Install a given module
    """
    _mage_module(module, env.current_release, action='install', force=force)


def _mage_module(module, release, action='install', force=False):
    """
    Internal method for installing community modules
    """
    install_kwargs = {
        'channelName': 'http://connect20.magentocommerce.com/community',
        'packageName': module,
        'action': action,
        'force': '',
    }

    if force:
        install_kwargs['force'] = '--force'

    with cd(release):
        run('./mage {action} {channelName} {packageName} {force}'.format(
            **install_kwargs))
