hamster2toggl
=============

``hamster2toggl`` is a simple software (python script) that reads
entries from hamster_ and adds them to a selected project in toggl_.

This software is licensed under the AGPLv3.

To run it, just

* install python and curl

* edit ``hamster2toggl.config`` and replace the example values:

  * db: the location of the hamster database
  * key: the API token you see in toggl when you go to My Profile
  * pid: the project id that you see in the toggl url when you go to
    Settings/Projects and click on one of your projects
  * timezone: hours to add or substract from your entries in hamster
    to convert them to UTC
  * category: the hamster category (others will be ignored). If it has no
    value, all entries will be used.

* stop hamster

* execute ``hamster2toggl``::

    python hamster2toggl.py

.. _hamster: http://projecthamster.wordpress.com/about/
.. _toggl: https://www.toggl.com/
