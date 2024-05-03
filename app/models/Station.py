from app.config.db import db
from orator import Model, SoftDeletes
import pendulum

Model.set_connection_resolver(db)

class Station(SoftDeletes,Model):
    __table__   = 'stations' 
    __guarded__ = ['id']
    __dates__   = ['deleted_at']

    def fresh_timestamp(self):
        return pendulum.now("Asia/Jakarta")