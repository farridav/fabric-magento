from fabric.api import task, local, lcd, env


@task
def provision(args=''):
    """
    Provision the box using ansible, optionally pass in some args,
    e.g:

        ``fab use:vagrant provision:'--tags env'``

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
