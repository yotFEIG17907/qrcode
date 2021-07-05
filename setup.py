from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='qrcode',
    version='1.0.0',
    packages=['prototypes'],
    url='',
    install_requires=required,
    license='GPL License v3.0',
    author='kenm',
    author_email='kamstdby@comcast.net',
    description='Play music via QRCode and RFID'
)
