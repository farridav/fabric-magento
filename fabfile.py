import os

from fabric.api import task, puts, local, env, cd, lcd, execute
from fabric.operations import run, put, open_shell, sudo, get
from fabric.colors import green
from fabric.context_managers import quiet
from fabric.contrib.files import exists


@task
def deploy(id='HEAD'):
    puts(green('Beginning deploy...'))
    git_hash = local('git rev-parse {}'.format(id), capture=True)
    package = build_package(git_hash, 'site')

    puts(green('Deploying release...'))
    release = deploy_package(package, os.path.join(env.release_dir, git_hash))

    puts(green('Installing Dependencies...'))
    install_dependencies(release)

    puts(green('Making symlinks...'))
    making_symlinks(release)

    puts(green('Set permissions...'))
    set_permissions(release)

    puts(green('Switching Release...'))
    switch_release(release)

    execute(restart_server)


def build_package(id, paths):
    """
    Locally compress the git repo into an archive
    """
    git_hash = local('git rev-parse {0}'.format(id), capture=True)
    package = '{0}.tar.gz'.format(git_hash)
    local('git archive --format tar.gz {0} -o {1} {2}'.format(
          id, package, paths))
    return package


def deploy_package(package, release):
    """
    Upload the package to the current_release location,
    decompress it and remove the compressed package
    """
    run('mkdir -p {}'.format(release))

    # Get magento core files in release
    run('rsync -az {}/ {}/'.format(env.mage_src, release))

    # now upload our local files over the top
    put(package, release)

    with cd(release):
        run('tar -xf {0}'.format(package))
        run('rsync -az site/ ./ && rm -rf site')
        run('rm -rf {}'.format(package))

    local('rm {0}'.format(package))

    return release


def install_dependencies(release):
    """
    Install required Magento modules into the given release, relies on there
    being a modules.txt in the project root, items prefixed with `#` are
    ignored
    """
    with cd(release):
        requirements = run('cat modules.txt')
        for module in requirements.split():
            if not module.startswith('#'):
                _mage_module(module, release, action='install', force=True)


def making_symlinks(release):
    """
    Make the required symlinks
    """
    symlinks = {
        os.path.join(release, 'media'): env.media_dir
    }

    for symlink, directory in symlinks.items():
        if exists(symlink):
            run('rm -rf {}'.format(symlink))

        run('ln -sfn {} {}'.format(directory, symlink))


def set_permissions(release):
    """
    Ensure our new files are owned by the application user and have the group
    that the webserver is running as
    """
    sudo('chown -R {}:www-data {}'.format(env.unix_user, release))


def switch_release(new_release):
    """
    Switch current and previous symlink so the newly deployed code is live
    """
    with quiet():
        previous_release = run('readlink {}'.format(env.current_release))
        run('ln -sfn {} {}'.format(previous_release, env.previous_release))

    run('ln -sfn {0} {1}'.format(new_release, env.current_release))


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
def copy_media():
    local('rsync -avz site/media/ {}@{}:{}'.format(
          env.user, env.host, env.media_dir))


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


@task
def provision(args=''):
    """
    Provision the box using ansible, optionally pass in some args,
    e.g:

        ``fab vagrant provision:'--tags env'``

    """
    with lcd('provisioning'):
        local('ansible-playbook {} {}'.format(env.playbook, args))


@task
def vm(command='list-commands'):
    """
    Use this projects virtual machine with arbitrary commands
    e.g:
        ``fab vm:up``

    """
    with lcd('provisioning'):
        local('vagrant {}'.format(command))
