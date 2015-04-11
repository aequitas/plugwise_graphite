from setuptools import setup

setup(
    name = "plugwise_graphite",
    version = "0.0.1",
    author = "Johan Bloemberg",
    author_email = "mail@ijohan.nl",
    description = ("Read metrics from plugwise circles and push to graphite."),
    license = "BSD",
    packages=['plugwise_graphite'],
    install_requires=[
        "plugwiselib",
        "anyconfig",
        "pyserial",
        "crcmod",
        "pyyaml",
    ],
    dependency_links=[
        "hg+https://bitbucket.org/hadara/python-plugwise#egg=plugwiselib"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    entry_points={
        'console_scripts': [
            'plugwise_graphite = plugwise_graphite.__init__:main',
        ],
    },
)