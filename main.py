import asyncio
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.exc import IntegrityError


engine = create_async_engine('sqlite+aiosqlite:///library.db')


# add enforcement for foreign keys
@event.listens_for(engine.sync_engine, "connect")
def enable_sqlite_fks(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


Base = declarative_base()


class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)


class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, unique=True, nullable=False)
    author_id = Column(Integer, ForeignKey(Author.id), nullable=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def create_book():
    book = Book(title="Book 1", author_id=1)
    async with session_maker() as session:
        session.add(book)
        try:
            await session.commit()
        except IntegrityError as e:
            msg = str(e.orig)
            if "FOREIGN KEY" in str(e.orig):
                # don't expose the db
                msg = 'foreign key constraint failed.'
            raise Exception(msg)


async def main():
    await init_db()

    try:
        await create_book()
    except Exception as e:
        print(f'Failed to create book: {e}')

if __name__ == "__main__":
    asyncio.run(main())
