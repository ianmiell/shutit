:orphan:


.. ShutIt documentation master file, created by
   sphinx-quickstart on Fri Jul 18 17:17:10 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. .. _contents:

ShutIt
======

.. topic:: Introduction

  Complex Docker Deployments Made Simple
  
  ShutIt is a tool for managing your build process that is both structured and flexible:
  
  Structured:
  
  - Modular structure
  - Manages the startup and setup of your container ready for the build
  - Has a lifecycle that can manage different parts of the lifecycle, eg:
      - Pre-requisites check
      - "Already installed?" check
      - Gather config
      - Start module
      - Stop module
      - Test module
      - Finalize container
  - Allows you to set config
  - Allows you to manage modules per distro (if needed)
  - Forces you to define an order for the modules
  - Puts record of build process into container
  - Enables continuous regression testing
  
  Flexible:
  
  - Modules model shell interactions, with all the freedom and control that implies
  - Modules can be plugged together like lego
  - GUI allows to you build and download images for your own needs (see http://shutit.tk)
  - Module scripts are in python, allowing full language control
  - Many helper functions for common interaction patterns
  - Can pause during build or on error to interact, then continue with build


.. seealso:: Other Documentation

    Download an offline copy of the latest ShutIt documentation:

    * `PDF`_
    * `ePub`_

    See documentation for past Salt releases at http://shutit.readthedocs.org.
    Download offline copies on the `ReadTheDocs download page`_.

.. _`PDF`: https://media.readthedocs.org/pdf/shutit/latest/shutit.pdf
.. _`ePub`: https://media.readthedocs.org/epub/shutit/latest/shutit.epub
.. _`ReadTheDocs download page`: https://readthedocs.org/projects/shutit/downloads/


Download
========



Getting Started
===============


ShutIt in depth
===============

Developer Docs
==============

:doc:`Docs <source/docs/index>`

Read man

Subtopic1
---------

**Subtopic2**

.. .. automodule:: shutit_global
   .. automodule:: setup
   .. automodule:: shutit_module
   .. automodule:: shutit_srv
   .. automodule:: util
   .. automodule:: package_map
   .. automodule:: emailer

.. .. toctree::
   :maxdepth: 2

More information about the project
==================================

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

