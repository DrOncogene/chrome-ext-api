from os import getenv

from fabric import task
from fabric.connection import Context
from invoke import run as local


DEPLOY_DIR = '/app/chrome_ext_api'
USER = getenv('REMOTE_USER', default='mypythtesting')


@task
def ping_server(ctx: Context):
    """Ping the server"""
    ctx.run("ping -c 2 localhost", echo=True, warn=True)


@task
def package_app(ctx: Context, path: str):
    """create a tarball of the application"""
    local('rm -rf .deployments', echo=True)
    local('mkdir -p .deployments', echo=True)
    local(
        f"tar -czvf .deployments/backend.tar.gz --exclude='.git' "
        f"--exclude='.venv' --exclude='Pipfile*' --exclude='.env.sample' "
        f"--exclude='.vscode' --exclude='*__pycache__*' --exclude='~'"
        f"--exclude='.deployments' {path}",
        echo=True
    )


@task
def copy_files(ctx: Context):
    """Copy the application to the server"""
    ctx.run(f'sudo rm -rf {DEPLOY_DIR}', echo=True)
    ctx.run(f'sudo mkdir -p {DEPLOY_DIR}', echo=True)
    ctx.put('.deployments/backend.tar.gz', '/tmp/')
    ctx.run(f'sudo tar -xvf /tmp/backend.tar.gz -C {DEPLOY_DIR}', echo=True)
    ctx.run(f'sudo chown -R {USER}:{USER} {DEPLOY_DIR}', echo=True)


@task
def server_setup(ctx: Context):
    """Start the application server"""
    with ctx.cd(f"{DEPLOY_DIR}"):
        ctx.run('./server.sh', echo=True)


@task
def deploy(ctx: Context):
    """Deploy the application"""
    ping_server(ctx)
    package_app(ctx, './')
    copy_files(ctx)
    server_setup(ctx)
