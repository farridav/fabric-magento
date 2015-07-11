import os
from fabric.api import task, local, lcd, env


@task
def provision(args=''):
    """
    Provision the box using ansible, optionally pass in some args,
    e.g:

        ``fab use:vagrant provision:'--tags env'``

    """
    with lcd(os.path.join(env.root, 'provisioning')):
        local('ansible-playbook {} {}'.format(env.playbook, args))


@task
def vm(command='list-commands'):
    """
    Use this projects virtual machine with arbitrary commands
    e.g:
        ``fab vm:up``

    """
    vagrant_directory = os.path.join(
        env.root, 'provisioning', os.path.dirname(env.playbook)
    )
    with lcd(vagrant_directory):
        local('vagrant {}'.format(command))
