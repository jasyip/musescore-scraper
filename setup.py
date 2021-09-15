from setuptools import setup, find_packages


with open("requirements.txt") as f:
    setup(
        install_requires=f.readlines()

    )
