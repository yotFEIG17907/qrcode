from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='music_player',
    version='1.0.0',
    packages=find_packages(where="./src"),
    package_dir={'': 'src'},
    url='',
    install_requires=required,
    license='GPL License v3.0',
    author='kenm',
    author_email='kamstdby@comcast.net',
    description='Play music, choices chosen via QRCode and RFID',
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires='>=3.7',
    entry_points={
        'console_scripts': ['music_player=client_player.sub_mqtt_driver:main',
                            'text_to_speech=speech.mqtt_to_speech:main']
    }
)
