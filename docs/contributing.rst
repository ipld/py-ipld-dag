Contributing
------------

Thank you for your interest in contributing! We welcome all contributions no matter
their size. Please read along to learn how to get started. If you get stuck, feel free
to ask for help in `Libp2p Discover Server <https://discord.gg/GK8TxRNh2s>`_.

Setting the stage
~~~~~~~~~~~~~~~~~

To get started, fork the repository to your own GitHub account, then clone it
to your development machine:

.. code:: sh

    git clone git@github.com:your-github-username/py-ipld-dag.git

Next, install the development dependencies and set up the project. We recommend using a
virtual environment, such as `virtualenv <https://virtualenv.pypa.io/en/stable/>`_ or
Python's built-in ``venv`` module. Instructions vary by platform:

Linux Setup
^^^^^^^^^^^

Prerequisites
"""""""""""""

On Debian Linux, install ``make`` if needed (e.g. for ``make test``, ``make docs-ci``):

.. code:: sh

    sudo apt install make

Setup Steps
"""""""""""

Install the development dependencies using a virtual environment:

**Option 1: Using uv (recommended, same as CI):**

First, install ``uv`` if you haven't already:

.. code:: sh

    curl -LsSf https://astral.sh/uv/install.sh | sh

Or using pip:

.. code:: sh

    pip install uv

Then set up the development environment:

.. code:: sh

    cd py-ipld-dag
    uv venv venv
    source venv/bin/activate
    uv pip install --upgrade pip
    uv pip install --group dev -e .
    pre-commit install

**Option 2: Manual setup with pip:**

.. code:: sh

    cd py-ipld-dag
    python3 -m venv ./venv
    . venv/bin/activate
    pip install --upgrade pip  # Ensure pip >= 25.1 for PEP 735 support
    pip install --group dev -e .
    pre-commit install

**Note:** This project uses PEP 735 ``[dependency-groups]`` which requires pip >= 25.1.
If you have an older pip version, upgrade it first.

An alternative using ``virtualenv``:

.. code:: sh

    cd py-ipld-dag
    virtualenv -p python venv
    . venv/bin/activate
    pip install --upgrade pip  # Ensure pip >= 25.1 for PEP 735 support
    pip install --group dev -e .
    pre-commit install

macOS Setup
^^^^^^^^^^^

Prerequisites
"""""""""""""

On macOS, ``make`` is usually already available (e.g. via Xcode Command Line Tools: ``xcode-select --install``). No other system packages are required.

Setup Steps
"""""""""""

Install the development dependencies using a virtual environment:

**Option 1: Using uv (recommended, same as CI):**

First, install ``uv`` if you haven't already:

.. code:: sh

    curl -LsSf https://astral.sh/uv/install.sh | sh

Or using Homebrew:

.. code:: sh

    brew install uv

Or using pip:

.. code:: sh

    pip install uv

Then set up the development environment:

.. code:: sh

    cd py-ipld-dag
    uv venv venv
    source venv/bin/activate
    uv pip install --upgrade pip
    uv pip install --group dev -e .
    pre-commit install

**Option 2: Manual setup with pip:**

.. code:: sh

    cd py-ipld-dag
    python3 -m venv ./venv
    . venv/bin/activate
    pip install --upgrade pip  # Ensure pip >= 25.1 for PEP 735 support
    pip install --group dev -e .
    pre-commit install

**Note:** This project uses PEP 735 ``[dependency-groups]`` which requires pip >= 25.1.
If you have an older pip version, upgrade it first.

An alternative using ``virtualenv``:

.. code:: sh

    cd py-ipld-dag
    virtualenv -p python venv
    . venv/bin/activate
    pip install --upgrade pip  # Ensure pip >= 25.1 for PEP 735 support
    pip install --group dev -e .
    pre-commit install

Windows Development Setup
^^^^^^^^^^^^^^^^^^^^^^^^^

Prerequisites
"""""""""""""

1. **Python 3.10+**
   - Download and install Python from `python.org <https://www.python.org/downloads/>`_ or the Microsoft Store.
   - Verify installation:

   .. code:: powershell

        python --version

2. **Git**
   - Install Git using Windows Package Manager (``winget``) or download from `git-scm.com <https://git-scm.com/download/win>`_.
   - Verify:

   .. code:: powershell

        winget install --id Git.Git -e
        git --version

3. **Make**
    - Option 1: Use Git Bash (included with Git) as a shell.
    - Option 2: Install ``make`` via Chocolatey (install Chocolatey first if needed: `choco.io <https://chocolatey.org/install>`_).
    - Verify installation:

   .. code:: powershell

        choco install make
        make --version


Setup Steps
"""""""""""

1. **Clone the Repository**
   - Open PowerShell or Git Bash and run:

   .. code:: powershell

        git clone git@github.com:your-github-username/py-ipld-dag.git
        cd py-ipld-dag

2. **Create a Virtual Environment**
   - In PowerShell:

   .. code:: powershell

        python -m venv venv
        .\venv\Scripts\activate

3. **Install Dependencies**

   **Option A: Using uv (recommended, same as CI):**

   First, install ``uv`` if you haven't already:

   .. code:: powershell

        # Using pip
        pip install uv

        # Or using winget
        winget install --id=astral-sh.uv

   Then set up the development environment:

   .. code:: powershell

        uv venv venv
        .\venv\Scripts\activate
        uv pip install --upgrade pip
        uv pip install --group dev -e .
        pre-commit install

   **Option B: Using pip:**

   .. code:: powershell

        pip install --upgrade pip  # Ensure pip >= 25.1 for PEP 735 support
        pip install --group dev -e .
        pre-commit install

   **Note:** This project uses PEP 735 ``[dependency-groups]`` which requires pip >= 25.1.
   If you have an older pip version, upgrade it first.

4. **Verify Setup**
   - Run the tests to ensure everything works:

   .. code:: powershell

        pytest -v

   - If using ``make test`` with Git Bash:

   .. code:: bash

        make test

Notes
"""""

- Use PowerShell, Command Prompt, or Git Bash as your shell.
- Ensure all tools (Python, Git, CMake) are in your system PATH.

Requirements
^^^^^^^^^^^^

The protobuf description in this repository was generated by ``protoc`` at version
``30.1``.

Running the tests
~~~~~~~~~~~~~~~~~

A great way to explore the code base is to run the tests.

We can run all tests with:

.. code:: sh

    make test


Code Style
~~~~~~~~~~

We use `pre-commit <https://pre-commit.com/>`_ to enforce a consistent code style across
the library. This tool runs automatically with every commit, but you can also run it
manually with:

.. code:: sh

    make lint

If you need to make a commit that skips the ``pre-commit`` checks, you can do so with
``git commit --no-verify``.

This library uses type hints, which are enforced by the ``mypy`` tool (part of the
``pre-commit`` checks). All new code is required to land with type hints, with the
exception of code within the ``tests`` directory.

Adding Examples
~~~~~~~~~~~~~~~

Organize examples in a package-style layout
(one package directory per example) and follow the workflow below.

To add a new example (actual ``py-ipld-dag`` example: ``cid_interface``):

1. Create a package directory in ``examples/cid_interface``.
2. Create ``examples/cid_interface/cid_interface.py`` with the example code.
3. Add ``examples/cid_interface/__init__.py`` so it is importable as a package.
4. Add/update an examples index page in docs (for example ``docs/examples.rst``), and
   include it from ``docs/index.rst``.
5. Add example tests (for example ``tests/examples/test_cid_interface.py``).
6. Add dedicated docs page for the example (for example ``docs/examples.cid_interface.rst``).
7. Add or update the examples list in ``examples/README.md`` and ``README.md``.
8. Add a newsfragment under ``newsfragments/`` using
   ``<ISSUE_OR_PR_NUMBER>.<TYPE>.rst`` when the change is user-facing.
9. Optionally expose it as a CLI script via ``pyproject.toml`` ``[project.scripts]``
   (``py-ipld-dag`` uses ``pyproject.toml``, not ``setup.py``).
10. Run project checks:

    .. code:: sh

        make pr
        make docs-ci

Actual py-ipld-dag example (package-style layout)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Example file: ``examples/cid_interface/cid_interface.py``

.. literalinclude:: ../examples/cid_interface/cid_interface.py
   :language: python

Run it:

.. code:: sh

    source venv/bin/activate
    python -m examples.cid_interface.cid_interface
    python -m examples.cid_interface.cid_interface --json

Pull Requests
~~~~~~~~~~~~~

It's a good idea to make pull requests early on. A pull request represents the start of
a discussion, and doesn't necessarily need to be the final, finished submission.

GitHub's documentation for working on pull requests is
`available here <https://docs.github.com/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests>`_.

Once you've made a pull request, take a look at the GitHub Actions build status in the
GitHub interface and make sure all tests are passing. In general pull requests that
do not pass the CI build yet won't get reviewed unless explicitly requested.

If the pull request introduces changes that should be reflected in the release notes,
please add a newsfragment file as explained
`here <https://github.com/ipld/py-ipld-dag/blob/master/newsfragments/README.md>`_.

If possible, the change to the release notes file should be included in the commit that
introduces the feature or bugfix.

Releasing
~~~~~~~~~

Releases are typically done from the ``master`` branch.
This project defines ``make notes`` and ``make release`` in the repository
``Makefile``.

Final test before each release
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before releasing a new version, build and test the package:

.. code:: sh

    git checkout master && git pull
    python -m build && pip install dist/*.whl  # or install from dist/ and test

This will build the package and install it in a temporary virtual environment. Follow
the instructions to activate the venv and test whatever you think is important.

You can also preview the release notes:

.. code:: sh

    towncrier --draft

Build the release notes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before bumping the version number, build the release notes (consumes newsfragments and
updates ``docs/release_notes.rst``):

.. code:: sh

    make notes bump=PART

Use ``PART`` as ``patch``, ``minor``, or ``major``. This generates the release notes for
the upcoming version and commits the result.

Bump version and tag
^^^^^^^^^^^^^^^^^^^^

Bump the version, build the package, push the release commit and tag, and upload to
PyPI:

.. code:: sh

    make release bump=PART

where ``PART`` is ``patch``, ``minor``, or ``major``. This creates a version bump
commit and tag (e.g. ``v0.1.1``), builds the package, pushes the commit and tag, and
uploads the distribution.

Which version part to bump
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``PART`` must be one of: ``major``, ``minor``, or ``patch`` (this project uses
``{major}.{minor}.{patch}`` only).

To issue an unstable version when the current version is stable, specify the new version
explicitly, e.g. ``bump-my-version bump --new-version 0.2.0-alpha.1``.

To preview the next version without changing any files, use
``bump-my-version show -i PART new_version`` where ``PART`` is ``patch``, ``minor``, or
``major``. Example: ``bump-my-version show -i patch new_version`` prints ``0.1.1``.
