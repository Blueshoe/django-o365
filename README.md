[![Tests Status](./reports/junit/tests-badge.svg?dummy=8484744)](./reports/junit/report.html)
[![Coverage Status](./reports/coverage/coverage-badge.svg?dummy=8484744)](./reports/coverage/htmlcov/index.html)
[![Flake8 Status](./reports/flake8/flake8-badge.svg?dummy=8484744)](./reports/flake8/index.html)
# django-o365
Simple EmailBackend for Django to work with Microsoft Exchange Online, via o365 package.

## Supported authentication
Currently only OAuth2.0 authentication with `credentials` workflow is supported.

## Configuration
Following Django settings need to be added:
```python
EMAIL_O365_TENANT_ID = 'my-client'
EMAIL_O365_CLIENT_ID = 'my-client-id'
EMAIL_O365_CLIENT_SECRET = 'super-secret'
EMAIL_O365_SENDER = 'mysender@example.com'

# set backend
EMAIL_BACKEND = 'django_o365.backend.O365EmailBackend'
```

## Badges
Badges have been created with [genbadge](https://github.com/smarie/python-genbadge):
```bash
# pytest
pytest --junitxml=reports/junit/junit.xml --html=reports/junit/report.html
genbadge tests

# coverage
coverage run -m pytest tests/
coverage xml
coverage html
genbadge coverage

# flake8
flake8 django_o365/ --exit-zero --format=html --htmldir ./reports/flake8 --statistics --tee --output-file flake8stats.txt
genbadge flake8
```
