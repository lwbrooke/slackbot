from setuptools import setup, find_packages

with open('requirements.txt') as f_in:
    install_requires = [l.strip() for l in f_in.readlines()]

with open('README.md') as f_in:
    long_description = f_in.read()

setup(
    name='fanghorn',
    version='0.0.1',
    description='Slackbot for personal use',
    long_description=long_description,
    url='https://github.com/lwbrooke/slackbot',
    license='Apache',
    author='Logan Brooke',
    packages=find_packages(),
    package_data={
        'fanghorn': ['config_files/*.yaml']
    },
    entry_points={
        'console_scripts': [
            'fanghorn = fanghorn.__main__:main'
        ]
    },
    install_requires=install_requires,
    setup_requires=[
        'wheel'
    ]
)