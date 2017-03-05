from setuptools import setup

setup(name='flac_phobic',
        version='0.1',
        description='export foobar playlists, re-encoding flac files as mp3.',
        url='https://github.com/david-cako/flac-phobic',
        author='david cako',
        author_email='dc@cako.io',
        license='GPLv3',
        packages=['flac_phobic'],
        entry_points={
            "console_scripts": ['flac_phobic = flac_phobic.flac_phobic:main']
        },
        install_requires={
            'requests',
            'unidecode',
        }
)

