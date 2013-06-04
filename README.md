hamster2toggl
=============

hamster2toggl is a simple software (python script) that read entries from
hamster ( http://projecthamster.wordpress.com/about/ ) and add them to a
selected project in toggl ( https://www.toggl.com )

This solftware is licensed under the AGPLv3.

To run it, just

- install python and curl

- edit hamster2toggl.config and replace the example values:

    - db: the location of the hamster database
    - key: the API token you see in toggl when you go to My Profile
    - pid: the project id that you see in the toggl url when you go to
      Settings/Projects and click one of your projects
    - timezone: hours to add or substract from your entries in hamster
      to convert them to UTC

- stop hamster

- execute hamster2toggl::

    python hamster2toggl.py
