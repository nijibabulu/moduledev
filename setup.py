from setuptools import setup

setup(
    name='moduledev',
    version='0.1',
    packages=['moduledev'],
    #url='https://bitbucket.org/bobzimmermann/model_selector',
    license='MIT',
    install_requires=['click','PyYAML','colorama'],
    entry_points={
        'console_scripts': ['moduledev=moduledev.cli:moduledev']
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
      ],
    author='Bob Zimmermann',
    author_email='robert.paul.zimmermann@gmail.com',
    description='''
A set of utilities for developing environment modules
'''
)
