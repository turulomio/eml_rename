# New Release Procedure
  1. Change version in pyproject.toml
  2. Change __version__ in __init__.py
  3. Add changelog to README.md
  4. Make a comit with the form eml_rename-$NEWVERSION$
  5. git push
  6. Create a new release setting $NEWVERSION$
  7. poetry build
  8. poetry publish --username --password
