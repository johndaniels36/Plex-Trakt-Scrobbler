from playhouse.apsw_ext import *


def migrate(migrator, database):
    # PlexAccount
    migrator.add_column('plex.account', 'refreshed_at', DateTimeField(null=True))

#
# Schema specification (for migration verification)
#

SPEC = {
    'plex.account': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER NOT NULL',

        'username':                 'VARCHAR(255)',
        'thumb':                    'TEXT',

        'refreshed_at':             'DATETIME'
    }
}
