from app.config.db import db
from orator import Model, SoftDeletes
import pendulum

Model.set_connection_resolver(db)

class StationSourceUrl(SoftDeletes,Model):
    __table__   = 'station_source_urls' 
    __guarded__ = ['id']
    __dates__   = ['deleted_at']

    def fresh_timestamp(self):
        return pendulum.now("Asia/Jakarta")