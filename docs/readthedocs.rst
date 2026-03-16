ReadTheDocs
===========

The project is configured for ReadTheDocs via ``.readthedocs.yaml`` in the repository root, aligned with the sister project `py-libp2p <https://github.com/libp2p/py-libp2p>`__:

- **Build:** Ubuntu 22.04, Python 3.10
- **Install:** ``pip install -e ".[docs,test]"`` (Sphinx, myst-parser, test deps)
- **Sphinx:** ``docs/conf.py``, ``fail_on_warning: true``
- **Formats:** HTML, epub, htmlzip

To connect and build on ReadTheDocs:

1. Go to https://readthedocs.org and sign in.
2. Click **Import a Project** and select the **ipld/py-ipld-dag** repository (or your fork).
3. Use the default settings; ReadTheDocs will detect ``.readthedocs.yaml``.
4. Trigger a build and confirm the docs URL (e.g. https://py-ipld-dag.readthedocs.io/) works.
5. Optionally enable **Build pull requests** for docs previews on PRs.

If the build fails, check the build log for Sphinx or dependency errors. Ensure the docs build passes locally with ``make docs-ci``.
