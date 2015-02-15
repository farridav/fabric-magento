import os

from fabric.api import task, puts, local, env, cd, execute
from fabric.operations import run, put, sudo
from fabric.colors import green
from fabric.context_managers import quiet
from fabric.contrib.files import exists

from .utils import restart_server, _mage_module


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
    symlink_persistent_dirs(release)

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


def symlink_persistent_dirs(release):
    """
    Iterate a list of folders that are persistent between deploys, and symlink
    them to the current release
    """
    for target in env.persistent_dirs.split(','):
        link_name = os.path.join(release, os.path.split(target)[-1])

        # If the link_name exists, delete it
        if exists(link_name):
            run('rm -rf {}'.format(link_name))

        run('ln -sfn {} {}'.format(target, link_name))


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
