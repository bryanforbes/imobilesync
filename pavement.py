from paver.easy import *
import paver.virtual
import paver.setuputils
from paver import svn
from paver.setuputils import setup, find_package_data, find_packages

options = environment.options
setup(
    name='imobilesync',
    version='0.1',
    description='',
    author='Bryan Forbes',
    author_email='bryan@reigndropsfall.net',
    url='',
    install_requires=['vobject'],
    packages=['imobilesync', 'imobilesync.data'],
    package_data=find_package_data('imobilesync', package='imobilesync', only_in_packages=False),
    zip_safe=True,
    #test_suite='nose.collector',
    #setup_requires=['nose>=0.11'],
    entry_points="""
        [console_scripts]
        imobilesync = imobilesync.commands:main
    """
)
options(
    minilib=Bunch(
        extra_files=['virtual']
    ),
    virtualenv=Bunch(
        packages_to_install=["ipython"],
        paver_command_line='develop',
        unzip_setuptools=True
    )
)

@task
@needs(['minilib', 'generate_setup', 'setuptools.command.sdist'])
def sdist():
    """Generates the tar.gz"""
    pass

@task
def clean():
    """Cleans up the virtualenv"""
    for p in ('bin', 'build', 'dist', 'docs', 'include', 'lib', 'man',
            'share', 'imobilesync.egg-info'):
        pth = path(p)
        if pth.isdir():
            pth.rmtree()
        elif pth.isfile():
            pth.remove()
