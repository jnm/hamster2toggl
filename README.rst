hamster2toggl
=============

``hamster2toggl`` is a simple software (python script) that reads
entries from hamster_ and adds them to a selected project in toggl_.

This software is licensed under the AGPLv3.

To run it, just

* install python and curl

* edit ``hamster2toggl.config`` and replace the example values:

  * ``hamster_db``: the filename of the hamster database
  * ``toggl_key``: the API token you see in toggl when you go to My Profile
  * ``toggl_project_id``: the project id that you see in the toggl url when
    you go to Settings/Projects and click on one of your projects
  * ``timezone``: hours to add or substract from your entries in hamster
    to convert them to UTC
  * ``hamster_category``: the hamster category (others will be ignored). If it
    has no value, all entries will be used.

* stop hamster

* execute ``hamster2toggl``::

    python hamster2toggl.py

  The above will upload today's data. Instead::

    python hamster2toggl.py 1

  will upload yesterday's data, and::

    python hamster2toggl.py 23

  will upload the data of 23 days ago.

.. _hamster: http://projecthamster.wordpress.com/about/
.. _toggl: https://www.toggl.com/
