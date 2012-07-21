Spank
=====

Introduction
------------
Spank is a tool for receiving, indexing and browsing server and application logs. See [Spanklogs.org](http://spanklogs.org/) for further info.

Installation
------------

*Note*: There is a Virtualbox VM based distribution if all you want to do is test or play with it. Again, refer to [Spanklogs.org](http://spanklogs.org/) for the details.Also, note that it is recommended to look at the downloads section to get a _stable_ snapshot of the code, as the main branch might not work all the time due to the changes I do.

  1. Install and setup ElasticSearch, refer to the official docs at [elasticsearch.org](http://elasticsearch.org)
  2. Replace your current syslog daemon with syslog-ng, on debian based distribution it should be as easy as running
     the following command:
     ```
     $ sudo apt-get install syslog-ng
     ```

  3. Downlaod the latest tar.gz from https://github.com/msurdi/spank/downloads, extract, and cd to it.
     ```
     tar xvzf spank-x.x.tar.gz
     cd spank
     ```
  4. Ensure you are running python >= 2.7 and pip
     ```
     $ python -V
     Python 2.7.3
     $ pip --version
     pip 1.0 from /usr/lib/python2.7/dist-packages (python 2.7)
     ```
  5. Install python dependencies listed in the requirements.txt file:
     ```
     $ sudo pip install -r requirements.txt
     ```
  6. Install spank package
      ```
      $ sudo python setup.py install
      ```
  7. Install (if you don't have it already) supervisord, in debian based distros it should be as easy as:
     ```
     $ sudo apt-get install supervisor
     ```
  8. Copy and modify the example supervisor configuration file:
     ```
     $ sudo cp contrib/supervisor/spank.conf /etc/supervisor/conf.d/  # Check the file and adapt it to your needs
     ```
  9. Edit syslog-ng configuration to pipe log entries to spank forwarder.Restart syslog-ng.Look at the example syslog-ng
     config in contrib/syslog-ng/spank.conf.


Some things to keep in mind
   * Ensure syslog-ng is listening on port udp/514, on the _external_ ip address you want to send logs to
   * The _-L /dev/log_ part of the supervisor config example makes Spank own logs go over the local logging device. In the provided
     syslog-ng example file, we send to the index just what is received from the network. This way, we avoid an infinite loop that could
     happen if we generate logs when indexing, which are later indexed, which generate logs again, and so on.

Issues
------
If you found any problem, please, submit a bug report at [https://github.com/msurdi/spank/issues/]

Tests
-----
Currently there are not so many tests as it should, but you can run the existing python one by running:

```
$ python -m unittest discover
```

in the root of the project. Ensure you have installed the python modules _mock_ and _simplejson_ additionaly to the ones in
requirements.txt file.


License
-------
This software is licensed under the [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0.html)


