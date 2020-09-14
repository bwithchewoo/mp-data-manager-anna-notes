import os
DATA_MANAGER_BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_MANAGER_ADMIN = True

DATA_CATALOG_ENABLED = True

DATA_CATALOG_NAME_FIELD = 'title'

CATALOG_TECHNOLOGY = 'Madrona'

CATALOG_SOURCE = None

ELASTICSEARCH_INDEX = 'metadata'

ELASTICSEARCH_SEARCH_FIELDS = [
    'title',
]
