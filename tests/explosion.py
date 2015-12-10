#!/bin/env python
import shutil
import unittest

from click.testing import CliRunner
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from alembic_migrate import migrations


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(128))


configurations = dict(database_uri='sqlite://',
                      target_metadata='tests.explosion:Base.metadata',
                      directory='migrations')


class TestBasic(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///app.db')

    def tearDown(self):
        shutil.rmtree('migrations', ignore_errors=True)

    def test_basic(self):
        runner = CliRunner()
        resp = runner.invoke(migrations, obj=configurations)
        self.assertEqual(resp.exit_code, 0)

    def test_migrate(self):
        runner = CliRunner()
        resp = runner.invoke(migrations, args=['init'], obj=dict(directory='migrations'))
        self.assertEqual(resp.exit_code, 0)
        resp = runner.invoke(migrations, args=['migrate'], obj=configurations)
        self.assertEqual(resp.exit_code, 0)
        resp = runner.invoke(migrations, args=['upgrade'], obj=configurations)
        self.assertEqual(resp.exit_code, 0)

