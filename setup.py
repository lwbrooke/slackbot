from setuptools import setup, find_packages

with open('requirements.txt') as f_in:
    lines = (l.strip() for l in f_in.readlines())
    install_requires = [l for l in lines if l and not l.startswith('--')]

with open('README.md') as f_in:
    long_description = f_in.read()

setup(
    name='fangorn',
    version='0.0.1',
    description='Slackbot for personal use',
    long_description=long_description,
    url='https://github.com/lwbrooke/slackbot',
    license='Apache',
    author='Logan Brooke',
    packages=find_packages(),
    package_data={
        'fangorn': ['config_files/*.yaml']
    },
    entry_points={
        'console_scripts': [
            'fangorn = fangorn.__main__:main'
        ]
    },
    install_requires=install_requires,
    setup_requires=[
        'wheel'
    ]
)
