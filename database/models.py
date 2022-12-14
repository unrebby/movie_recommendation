from database.database_configuration import db
import peewee
from uuid import uuid4


class BaseModel(peewee.Model):
    class Meta:
        database = db


class bot_users(BaseModel):
    uuid = peewee.UUIDField(primary_key=True, default=uuid4)
    telegram_id = peewee.BigIntegerField(null=False, unique=True)
    chat_id = peewee.BigIntegerField(null=False, unique=True)
    first_name = peewee.TextField(null=False)
    last_name = peewee.TextField(null=True)
    tg_username = peewee.TextField(null=True)

    class Meta:
        database = db


class films(BaseModel):
    uuid = peewee.UUIDField(primary_key=True, default=uuid4)
    name = peewee.TextField(null=False, unique=True)
    director = peewee.TextField(null=False)
    rating = peewee.FloatField(null=True)
    counter = peewee.IntegerField(null=True)
    year = peewee.IntegerField(null=False)
    language = peewee.TextField(null=True)
    duration = peewee.IntegerField(null=True)
    genre = peewee.TextField(null=True)

    class Meta:
        database = db


class actors(BaseModel):
    uuid = peewee.UUIDField(primary_key=True, default=uuid4)
    actor = peewee.TextField(null=False)
    film_name = peewee.ForeignKeyField(
        films, db_column="film_name", to_field="name", on_delete="CASCADE"
    )


class wish_list(BaseModel):
    uuid = peewee.UUIDField(primary_key=True, default=uuid4)
    film_name = peewee.ForeignKeyField(
        films, db_column="film_name", to_field="name", on_delete="CASCADE"
    )
    telegram_id = peewee.ForeignKeyField(
        bot_users, to_field="telegram_id", on_delete="CASCADE"
    )

    class Meta:
        database = db
