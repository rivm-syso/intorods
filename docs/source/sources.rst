
Import data sources
===================

.. .. argparse::
..     :filename: ../intorods.py
..     :func: get_argument_parser
..     :prog: intorods

To get a list of supported filessystems  and options:

``-l|--listfs``
    List supported filesystems and options

.. _section-source-local:

Local filesystem
----------------

This is the default source, and the easiest to configure, since it has no configuration options.

.. code-block:: console

    $ intorods '/home/user/mydata' '/demoZone/home/user/'

.. _section-source-smb:

SMB filesystem
--------------

``-s|--source_fs``
    To use the SMB/CIFS filesystem use the **smb** source_fs option.

``-o|--source_option``
    The **smb** source_fs needs the source_options for the SMB share:

    * server=<server>,
    * share=<sharename>,
    * nbserver=<netbios servername>,
    * username=<user>,
    * domain=<domain>,
    * password=<password>

    and a source_path, the path in the SMB share.

example:

.. code-block:: console

    $ intorods -s smb -o server='server1.localdomain',share='data',username='smbuser',password='secret' '/data/mydata' '/demoZone/home/user/'


.. _section-source-ftp:

FTP filesystem
--------------

``-s|--source_fs``
    To use the SFTP filesystem use the **ftp** source_fs option.

``-o|--source_option``
    The **ftp** source_fs needs the source_options for the FTP share:

    Mandatory option:

    * hostname=<hostname>

    Optional options:

    * username=<user>,
    * password=<password>

    If you do not provide credentials, **anonymous** login will be attempted

example:

.. code-block:: console

    $ intorods -s ftp -o hostname='server2.localdomain' '/home/ftpusers/data' '/demoZone/home/user/'


.. _section-source-sftp:

SFTP filesystem
---------------

``-s|--source_fs``
    To use the SFTP filesystem use the **sftp** source_fs option.

``-o|--source_option``
    The **sftp** source_fs needs the source_options for the SFTP share:

    * hostname=<hostname>,
    * username=<user>,
    * password=<password>

    and a source_path, the path in the SFTP share.

example:

.. code-block:: console

    $ intorods -s sftp -o hostname='server2.localdomain',user='sftpuser',password='secret' '/home/sftpusers/data' '/demoZone/home/user/'


.. _section-source-scp:

SCP filesystem
--------------

``-s|--source_fs``
    To use the SCP filesystem use the **scp** source_fs option.

``-o|--source_option``
    The **scp** source_fs needs the source_options for the SCP share:

    * hostname=<hostname>,
    * username=<username>

    SCP uses the secure ssh key to get acces to the share.
 
    and a source_path, the path in the SCP share.

example:

.. code-block:: console

    $ intorods -s scp -o hostname='server3.localdomain',user='sftpuser' '/home/user/data' '/demoZone/home/user/'


.. _section-source-irods:

iRODS instance
--------------

```-s|-source_fs``
    To use an iRODS instance use the **irods** source_fs option.

``-o|--source_option``
    The **irods** source_fs needs the source_options for the iRODS instance:

    * resource=<dest resource>,
    * authfile=<filename>,
    * timeout=<timeout>

    and a source_path, the path in the iRODS instance.

    authfile is a custom irods_environment file. 

example:

.. code-block:: console

    $ intorods -s irods -o resource='storageResc',authfile='my_irods_env.json',timeout='180' '/otherZone/projects/myProject' '/demoZone/home/user/'


