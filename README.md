# Fabric Magento

Fabric Deployment scripts for deploying to a Magento installation that has been
provisioned with [this project](https://github.com/farridav/ansible-magento)

To get setup for working on this project you will need fabric installed

NOTE: This does not currently go into any detail about how to setup your local
environment for provisioning, I will do a better job on this ASAP

## Project setup (Not including provisioning or local dev)

```
    fabfile/ (this repo)
    site/ (Your* Magento files)
```

* NOT Magento core, just your theme, local modules etc.

## Deployment
Ensure you have made an env.yml in your project root, example below:

```
    ---

    environments:
      stage:
          user: my_applications_user
          hosts:
            - 12.34.567.890
```

Then deploy to it with `fab stage deploy`

## Useful Commands

### List off all available fab tasks
`fab -l`

### List off all available environments
`fab env`

### Steal the DB from the given environment
`fab use:<environment> get_db`

### Load a DB into the given environment
`fab use:<environment> put_db`

### Sync your local files with the given environment every second
`fab use:<environment> develop`

### Drop into a shell on the given environment
`fab use:<environment> shell`

### Drop into a mysql shell on the given environment
`fab use:<environment> dbshell`

### Update the Magento core (Used for all subsequent deploys)
`fab use:<environment> update_magento_core`
