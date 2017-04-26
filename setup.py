from setuptools import setup, find_packages

setup(
    name='myjenkins',
    version='0.0.2',
    url='https://github.com/secretescapes/myjenkins',
    author='Joshua Prendergast',
    packages=find_packages(),
    install_requires=[
        'click',
        'jenkinsapi>=0.3.4',
    ],
    extras_require = {
        'pandas':  ["pandas"]
    },
    entry_points={
        'console_scripts': [
            'myjenkins=myjenkins.__main__:main',
        ],
    },
)
