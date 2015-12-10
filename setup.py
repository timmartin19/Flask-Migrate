"""
Flask-Migrate
--------------

SQLAlchemy database migrations for Flask applications using Alembic.
"""
from setuptools import setup


setup(
    name='vk-easy-alembic',
    version='1.6.1',
    url='http://github.com/miguelgrinberg/flask-migrate/',
    license='MIT',
    author='Miguel Grinberg',
    author_email='miguelgrinberg50@gmail.com',
    description=('SQLAlchemy database migrations for Flask applications '
                 'using Alembic'),
    long_description=__doc__,
    packages=['alembic_migrate'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'alembic>=0.6',
        'click'
    ],
    test_suite="tests",
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
