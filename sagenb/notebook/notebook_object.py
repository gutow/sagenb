# -*- coding: utf-8 -*
"""nodoctest
Configure and Start a Notebook Server

The :class:`NotebookObject` is used to configure and launch a Sage
Notebook server.
"""
#############################################################################
#       Copyright (C) 2007 William Stein <wstein@gmail.com>
#  Distributed under the terms of the GNU General Public License (GPL)
#  The full text of the GPL is available at:
#                  http://www.gnu.org/licenses/
#############################################################################

import time, os, shutil, signal, tempfile

import notebook as _notebook

import run_notebook

class NotebookObject:
    r"""
    Start the Sage Notebook server.  More details about using these
    options, as well as tips and tricks, may be available at `this
    Sage wiki page`_.  If a notebook server is already running in the
    directory, this will open a browser to the running notebook.

    INPUT:

        - ``directory`` -- string; directory that contains the Sage
          notebook files; the default is
          ``.sage/sage_notebook.sagenb``, in your home directory.

        - ``port`` -- integer (default: ``8080``), port to serve the
          notebook on.

        - ``interface`` -- string (default: ``'localhost'``), address
          of network interface to listen on; give ``''`` to listen on
          all interfaces.

        - ``port_tries`` -- integer (default: ``0``), number of
          additional ports to try if the first one doesn't work (*not*
          implemented).

        - ``secure`` -- boolean (default: ``False``) if True use https
          so all communication, e.g., logins and passwords, between
          web browsers and the Sage notebook is encrypted via SSL.  You
          must have OpenSSL installed to use this feature, or if you compile
          Sage yourself, have the OpenSSL development libraries installed.
          *Highly recommended!*
          
          When ``notebook()`` is run for first time with ``secure=True``, it
          will generate new keys and store them to ``.sage/notebook/``.
          Remove this when you want to generate new keys, for example if an
          older version of Sage has generated keys that are too short for
          current browsers.
          
        - ``site_name`` -- string (default: ``sage``) This string is the prefix
          to all the paths on the site.  This allows for clean proxying of
          multiple sage servers behind one domain name 
          (e.g. www.domain.org/sage0, www.domain.org/sage1, etc.).  Do not worry
          about this unless you are proxying sage behind an industrial server
          such as Apache2 or nginx.  The notebook server now handles virtual
          host monster syntax, so you can tell the sage server
          what absolute paths to insert in pages (see examples below).

        - ``reset`` -- boolean (default: ``False``) if True allows you
          to set the admin password.  Use this if you forget your
          admin password.

        - ``accounts`` -- boolean (default: ``False``) if True, any
          visitor to the website will be able to create a new account.
          If False, only the admin can create accounts (currently,
          this can only be done by running with ``accounts=True`` and
          shutting down the server properly (``SIG_INT`` or
          ``SIG_TERM``), or on the command line with, e.g.,

          ::

              from sagenb.notebook.notebook import load_notebook
              nb = load_notebook("directory_to_run_sage_in")
              user_manager = nb.user_manager()
              user_manager.set_accounts(True)
              user_manager.add_user("username", "password", "email@place", "user")
              nb.save()

        - ``automatic_login`` -- boolean (default: True) whether to pop up
          a web browser and automatically log into the server as admin.  You can
          override the default browser by setting the ``SAGE_BROWSER`` environment
          variable, e.g., by putting

          ::

              export SAGE_BROWSER="firefox"

          in the file .bashrc in your home directory.

        - ``upload`` -- string (default: None) Full path to a local file
          (sws, txt, zip) to be uploaded and turned into a worksheet(s).
          This is equivalent to manually uploading a file via
          ``http://localhost:8080/upload`` or to fetching
          ``http://localhost:8080/upload_worksheet?url=file:///...``
          in a script except that (hopefully) you will already be
          logged in.

          .. warning::

              If you are running a server for others to log into, set ``automatic_login=False``.
              Otherwise, all of the worksheets on the entire server will be loaded when the server
              automatically logs into the admin account.


        - ``timeout`` -- integer (default: 0) seconds until idle
          worksheet sessions automatically timeout, i.e., the
          corresponding Sage session terminates. 0 means "never
          timeout". If your server is running out of memory, setting a
          timeout can be useful as this will free the memory used by
          idle sessions.

        - ``doc_timeout`` -- integer (default: 600) seconds until idle
          live documentation worksheet sessions automatically timeout,
          i.e., the corresponding Sage session terminates.
          0 means "never timeout".

        - ``server_pool`` -- list of strings (default: None) list;
          this option specifies that worksheet processes run as a
          separate user (chosen from the list in the ``server_pool``
          -- see below).

    .. note::

       If you have problems with the server certificate hostname not
       matching, do ``notebook.setup()``.

    .. note::

       The ``require_login`` option has been removed.  Use ``automatic_login`` to control
       automatic logins instead---``automatic_login=False`` corresponds to ``require_login=True``.

    EXAMPLES:

    1. I just want to run the Sage notebook.  Type::

           notebook()

    2. I want to run the Sage notebook server on a remote machine and
       be the only person allowed to log in.  Type::

           notebook(interface='', secure=True)

       the first time you do this you'll be prompted to set an
       administrator password.  Use this to login. NOTE: You may have
       to run ``notebook.setup()`` again and change the hostname.
       ANOTHER NOTE: You must have installed pyOpenSSL in order to use
       secure mode; see the top-level Sage README file or the "Install
       from Source Code" section in the Sage manual for more
       information.

    3. I want to create a Sage notebook server that is open to anybody
       in the world to create new accounts. To run the Sage notebook
       publicly (1) at a minimum run it from a chroot jail or inside a
       virtual machine (see `this Sage wiki page`_) and (2) use a
       command like::

           notebook(interface='', server_pool=['sage1@localhost'],
           ulimit='-v 500000', accounts=True, automatic_login=False)

       The server_pool option specifies that worksheet processes run
       as a separate user.  The ulimit option restricts the memory
       available to each worksheet processes to 500 MB.  See help on
       the ``accounts`` option above.

       Be sure that ``sage_notebook.sagenb/users.pickle`` and the
       contents of ``sage_notebook.sagenb/backups`` are chmod
       ``og-rwx``, i.e., only readable by the notebook process, since
       otherwise any user can read ``users.pickle``, which contains
       user email addresses and account information (passwords are
       stored hashed, so fewer worries there). You will need to use
       the ``directory`` option to accomplish this.
       
    4. Set up a server proxied behind an industrial server such as Apache2 or
       nginx.
       
       Server named ``sage3`` running on port ``8082``.  Launch with the command::
       
           notebook(interface='', port=8082, site_name='sage3',
           automatic_login=False)
                    
       For an Apache2 server rewrite proxying in the configuration file
       will look something like the following::
           
           RewriteEngine on
            RewriteRule ^/sage3(.*) http://localhost:8082/virtualhostbase/http/localhost/sage3$1 [P]
       
       nginx example::
       
           TODO
       

    INPUT:  (more advanced)

        - ``server_pool`` -- list of strings (initial default: None),
          if given, should be a list like \['sage1@localhost',
          'sage2@localhost'\], where you have setup ssh keys so that
          typing::

              ssh sage1@localhost

          logs in without requiring a password, e.g., by typing
          ``ssh-keygen`` as the notebook server user, then putting
          ``~/.ssh/id_rsa.pub`` as the file ``.ssh/authorized_keys``.
          Note: you have to get the permissions of files and
          directories just right -- see `this Sage wiki page`_ for
          more details.

          Files between the main Sage process and the ``server_pool``
          workers are transferred through ``/tmp`` by default.  If the
          environment variable :envvar:`SAGENB_TMPDIR` or
          :envvar:`TMPDIR` exists, that directory is used instead.  This
          directory must be shared, so if the machines are separate the
          server machine must NFS-export ``/tmp`` or
          :envvar:`SAGENB_TMPDIR`.

        - ``server`` -- string ("twistd" (default) or "flask").  The server
          to use to server content.

        - ``profile`` -- True, False, or file prefix (default: False - no profiling),
          If True, profiling is saved to a randomly-named file like `sagenb-*-profile*.stats`
          in the $DOT_SAGE directory.  If a string, that string is used as a
          prefix for the pstats data file.

        - ``ulimit`` -- string (initial default: None -- leave as is),
          if given and ``server_pool`` is also given, the worksheet
          processes are run with these constraints. See the ulimit
          documentation. Common options include:

              - ``-t`` The maximum amount of cpu time in seconds.
                NOTE: For Sage, ``-t`` is the wall time, not cpu time.

              - ``-u`` The maximum number of processes available to a
                single user.

              - ``-v`` The maximum amount of virtual memory available
                to the process.

          Values are in 1024-byte increments, except for ``-t``, which
          is in seconds, and ``-u`` which is a positive
          integer. Example: ulimit="-v 400000 -t 30"

    .. note::

       The values of ``server_pool`` and ``ulimit`` default to what
       they were last time the notebook command was called.

    OTHER NOTES:

       - If you create a file ``\\$DOT_SAGE/notebook.css`` then it
         will get applied when rendering the notebook HTML.  This
         allows notebook administrators to customize the look of the
         notebook.  Note that by default ``\\$DOT_SAGE`` is
         ``\\$HOME/.sage``.

    .. _this Sage wiki page:  http://wiki.sagemath.org/StartingTheNotebook

    """
    def __call__(self, *args, **kwds):
        return self.notebook(*args, **kwds)

    notebook = run_notebook.notebook_run
    setup    = run_notebook.notebook_setup

notebook = NotebookObject()


def inotebook(*args, **kwds):
    """
    Exactly the same as ``notebook(...)`` but with ``secure=False``.
    """
    kwds['secure'] = False
    notebook(*args, **kwds)


def test_notebook(admin_passwd, secure=False, directory=None, port=8050,
                  interface='localhost', verbose=False):
    """
    This function is used to test notebook server functions.

    EXAMPLES::

        sage: from sagenb.notebook.notebook_object import test_notebook
        sage: passwd = str(randint(1,1<<128))
        sage: nb = test_notebook(passwd, interface='localhost', port=8060)
        sage: import urllib
        sage: h = urllib.urlopen('http://localhost:8060')
        sage: homepage = h.read()
        sage: h.close()
        sage: 'html' in homepage
        True
        sage: nb.dispose()
    """
    import socket, pexpect

    if directory is None:
        directory = tmp_dir = tempfile.mkdtemp()
    else:
        tmp_dir = None

    if not os.path.exists(directory):
        os.makedirs(directory)

    nb = _notebook.load_notebook(directory)
    nb.set_accounts(True)
    nb.add_user('admin', admin_passwd, '')
    nb.set_accounts(False)
    nb.save()

    p = notebook(directory=directory, accounts=True, secure=secure, port=port,
                 interface=interface, automatic_login=False, fork=True, quiet=True)
    p.expect("Starting factory")
    def dispose():
        try:
            p.send('\x03') # control-C
        except pexpect.EOF:
            pass
        p.close(force=True)
        shutil.rmtree(nb._dir)
    p.dispose = dispose
    if verbose:
        print "Notebook started."
    return p
