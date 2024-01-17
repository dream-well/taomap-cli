from setuptools import setup, find_packages

setup(
    name="taomap",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'taomap=taomap-cli.client:start_client',
        ],
    },
    install_requires=[
        # List your dependencies here
    ],
)
