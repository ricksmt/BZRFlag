#!/usr/bin/env python

from distutils.core import setup

setup(name='BZRFlag',
      version='1.0',
      description='BZRFlag: BZFlag with Robots!',
      author='BYU AML Lab',
      author_email='kseppi@byu.edu',
      url='http://aml.cs.byu.edu/',
      #download_url='',
      packages=['bzrflag', 'bzagents'],
      package_data = {'': ['*.png', '*.txt', '*.ttf']},
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Operating System :: POSIX :: Linux',
                   'Intended Audience :: Science/Research',
                   'License :: OSI Approved :: GNU General Public License (GPL)',
                   'Natural Language :: English',
                   'Programming Language :: Python',
                   'Topic :: Scientific/Engineering :: Artificial Intelligence'],
     )
