import sys
sys.path.insert(0, 'C:/Users/poove/Documents/New folder/backend')

from alembic.config import Config
from alembic import command

cfg = Config('C:/Users/poove/Documents/New folder/backend/alembic.ini')
command.upgrade(cfg, 'head')
print('Migration completed successfully')