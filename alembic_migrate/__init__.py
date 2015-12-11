import os
from functools import update_wrapper
import threading

import argparse
from alembic import __version__ as __alembic_version__
from alembic.config import Config as AlembicConfig
from alembic import command
import click


alembic_version = tuple([int(v) for v in __alembic_version__.split('.')[0:3]])


class Config(AlembicConfig):
    def get_template_directory(self):
        package_dir = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(package_dir, 'templates')


def _get_config(directory='migrations', x_arg=None, opts=None):
    config = Config(os.path.join(directory, 'alembic.ini'))
    config.set_main_option('script_location', directory)
    if config.cmd_opts is None:
        config.cmd_opts = argparse.Namespace()
    for opt in opts or []:
        setattr(config.cmd_opts, opt, True)
    if x_arg is not None:
        if not getattr(config.cmd_opts, 'x', None):
            setattr(config.cmd_opts, 'x', [x_arg])
        else:
            config.cmd_opts.x.append(x_arg)
    return config


def inject_directory(func):
    """
    A decorator to inject the directory into
    the function.

    :param func: The cli command to pass the config dictionary to.
    """
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        """
        Injects the directory into the CLI command
        """
        return ctx.invoke(func, ctx.obj['directory'], *args, **kwargs)
    return update_wrapper(new_func, func)


def inject_alembic_config(func):
    """
    A decorator to inject the alembic configuration into
    the function
    :param func: The function to decorate
    """
    @click.pass_context
    def wrapper(ctx, *args, **kwargs):
        """
        Inject the alembic config into the CLI Command
        """
        x_arg = kwargs.pop('x_arg', None)
        directory = ctx.obj['directory']
        config = _get_config(directory, x_arg=x_arg)
        config.set_main_option('sqlalchemy.url', ctx.obj['database_uri'])
        config.set_main_option('metadata', ctx.obj['target_metadata'])
        ctx.obj['config'] = config
        return ctx.invoke(func, config, *args, **kwargs)
    return update_wrapper(wrapper, func)


@click.group()
@click.pass_context
def migrations(ctx):
    pass

@migrations.command()
@click.option('--multidb', is_flag=True, help="Multiple databases migraton (default is False)")
@inject_directory
def init(directory, multidb):
    """Generates a new migration"""
    config = Config()
    config.set_main_option('script_location', directory)
    config.config_file_name = os.path.join(directory, 'alembic.ini')
    if multidb:
        command.init(config, directory, 'flask-multidb')
    else:
        command.init(config, directory, 'flask')


@migrations.command()
@click.option('--rev-id', default=None,
              help='Specify a hardcoded revision id instead of generating one')
@click.option('--version-path', default=None,
              help='Specify specific path from config for version file')
@click.option('--branch-label', default=None,
              help='Specify a branch label to apply to the new revision')
@click.option('--splice', is_flag=True, help='Allow a non-head revision as the "head" to splice onto')
@click.option('--head', default='head',
              help='Specify head revision or <branchname>@head to base new revision on')
@click.option('--sql', is_flag=True,
              help="Don't emit SQL to database - dump to standard output instead")
@click.option('--autogenerate', is_flag=True,
              help=('Populate revision script with andidate migration '
                    'operatons, based on comparison of database to model'))
@click.option('-m', '--message', default=None)
@inject_alembic_config
def revision(config, message=None, autogenerate=False, sql=False,
             head='head', splice=False, branch_label=None, version_path=None,
             rev_id=None):
    """Create a new revision file."""
    if alembic_version >= (0, 7, 0):
        command.revision(config, message, autogenerate=autogenerate, sql=sql,
                         head=head, splice=splice, branch_label=branch_label,
                         version_path=version_path, rev_id=rev_id)
    else:
        command.revision(config, message, autogenerate=autogenerate, sql=sql)


@migrations.command()
@click.option('--rev-id', default=None,
              help='Specify a hardcoded revision id instead of  generating one')
@click.option('--version-path', default=None,
              help='Specify specific path from config for version file')
@click.option('--branch-label', default=None,
              help='Specify a branch label to apply to the new revision')
@click.option('--splice', is_flag=True, default=False,
              help='Allow a non-head revision as the "head" to splice onto')
@click.option('--head', default='head',
              help='Specify head revision or <branchname>@head to base new revision on')
@click.option('--sql', is_flag=True, default=False,
              help="Don't emit SQL to database - dump to standard output instead")
@click.option('-m', '--message', default=None)
@inject_alembic_config
def migrate(config, message=None, sql=False, head='head', splice=False,
            branch_label=None, version_path=None, rev_id=None):
    """Alias for 'revision --autogenerate'"""
    setattr(config.cmd_opts, 'autogenerate', True)
    if alembic_version >= (0, 7, 0):
        command.revision(config, message, autogenerate=True, sql=sql, head=head,
                         splice=splice, branch_label=branch_label,
                         version_path=version_path, rev_id=rev_id)
    else:
        command.revision(config, message, autogenerate=True, sql=sql)


@migrations.command()
@click.argument('revision', required=False)
@inject_alembic_config
def edit(config, revision='current'):
    """Edit current revision."""
    if alembic_version >= (0, 8, 0):
        command.edit(config, revision)
    else:
        raise RuntimeError('Alembic 0.8.0 or greater is required')


@migrations.command()
@click.option('--rev-id', default=None,
              help='Specify a hardcoded revision id instead of generating one')
@click.option('--branch-label',  default=None,
              help='Specify a branch label to apply to the new revision')
@click.option('-m', '--message', default=None)
@click.argument('revisions', nargs=-1)
@inject_alembic_config
def merge(config, revisions='', message=None, branch_label=None, rev_id=None):
    """Merge two revisions together.  Creates a new migration file"""
    if alembic_version >= (0, 7, 0):
        command.merge(config, revisions, message=message,
                      branch_label=branch_label, rev_id=rev_id)
    else:
        raise RuntimeError('Alembic 0.7.0 or greater is required')


@migrations.command()
@click.option('-x', '--x-arg', default=None,
              help="Additional arguments consumed by custom env.py scripts")
@click.option('--tag', default=None,
              help="Arbitrary 'tag' name - can be used by custom env.py scripts")
@click.option('--sql', is_flag=True, default=False,
              help="Don't emit SQL to database - dump to standard output instead")
@click.argument('revision', required=False, default='head')
@inject_alembic_config
def upgrade(config, revision='head', sql=False, tag=None, x_arg=None):
    """Upgrade to a later version"""
    command.upgrade(config, revision, sql=sql, tag=tag)


@migrations.command()
@click.option('-x', '--x-arg', default=None,
              help="Additional arguments consumed by custom env.py scripts")
@click.option('--tag', default=None,
              help="Arbitrary 'tag' name - can be used by custom env.py scripts")
@click.option('--sql', is_flag=True, default=False,
              help="Don't emit SQL to database - dump to standard output instead")
@click.argument('revision', required=False, default="-1")
@inject_alembic_config
def downgrade(config, revision='-1', sql=False, tag=None, x_arg=None):
    """Revert to a previous version"""
    if sql and revision == '-1':
        revision = 'head:-1'
    command.downgrade(config, revision, sql=sql, tag=tag)


@migrations.command()
@click.argument('revision', required=False, default="head")
@inject_alembic_config
def show(config, revision='head'):
    """Show the revision denoted by the given symbol."""
    if alembic_version >= (0, 7, 0):
        command.show(config, revision)
    else:
        raise RuntimeError('Alembic 0.7.0 or greater is required')


@migrations.command()
@click.option('-v', '--verbose', is_flag=True,
              default=False, help='Use more verbose output')
@click.option('-r', '--rev-range', default=None,
              help='Specify a revision range; format is [start]:[end]')
@inject_alembic_config
def history(config, rev_range=None, verbose=False):
    """List changeset scripts in chronological order."""
    if alembic_version >= (0, 7, 0):
        command.history(config, rev_range, verbose=verbose)
    else:
        command.history(config, rev_range)


@migrations.command()
@click.option('--resolve-dependencies', is_flag=True, default=False,
              help='Treat dependency versions as down revisions')
@click.option('-v', '--verbose', is_flag=True,
              default=False, help='Use more verbose output')
@inject_alembic_config
def heads(config, verbose=False, resolve_dependencies=False):
    """Show current available heads in the script directory"""
    if alembic_version >= (0, 7, 0):
        command.heads(config, verbose=verbose,
                      resolve_dependencies=resolve_dependencies)
    else:
        raise RuntimeError('Alembic 0.7.0 or greater is required')


@migrations.command()
@click.option('-v', '--verbose', is_flag=True,
              default=False, help='Use more verbose output')
@inject_alembic_config
def branches(config, verbose=False):
    """Show current branch points"""
    if alembic_version >= (0, 7, 0):
        command.branches(config, verbose=verbose)
    else:
        command.branches(config)


@migrations.command()
@click.option('--head-only', is_flag=True, default=False,
              help='Deprecated. Use --verbose for additional output')
@click.option('-v', '--verbose', is_flag=True,
              default=False, help='Use more verbose output')
@inject_alembic_config
def current(config, verbose=False, head_only=False):
    """Display the current revision for each database."""
    if alembic_version >= (0, 7, 0):
        command.current(config, verbose=verbose, head_only=head_only)
    else:
        command.current(config)


@migrations.command()
@click.option('--tag', default=None,
              help="Arbitrary 'tag' name - can be used by custom env.py scripts")
@click.option('--sql', is_flag=True, default=False,
              help="Don't emit SQL to database - dump to standard output instead")
@click.argument('revision', default=None)
@inject_alembic_config
def stamp(config, revision='head', sql=False, tag=None):
    """'stamp' the revision table with the given revision; don't run any
    migrations"""
    command.stamp(config, revision, sql=sql, tag=tag)
