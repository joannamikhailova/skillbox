import os
import datetime
import enum
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, constr
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, select
import asyncpg

# --------------------
# Конфигурация БД
# --------------------
DB_HOST = os.getenv("FSTR_DB_HOST", "localhost")
DB_PORT = os.getenv("FSTR_DB_PORT", "5432")
DB_USER = os.getenv("FSTR_DB_LOGIN", "postgres")
DB_PASS = os.getenv("FSTR_DB_PASS", "1234")
DB_NAME = os.getenv("FSTR_DB_NAME", "fstr_db")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

ADMIN_DATABASE_URL = {
    "user": DB_USER,
    "password": DB_PASS,
    "database": "postgres",
    "host": DB_HOST,
    "port": DB_PORT,
}

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# --------------------
# Модели SQLAlchemy
# --------------------
class PassStatus(str, enum.Enum):
    new = "new"
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    fam = Column(String, nullable=False)
    name = Column(String, nullable=False)
    otc = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    passes = relationship("Pass", back_populates="user")

class Pass(Base):
    __tablename__ = "pass"
    id = Column(Integer, primary_key=True, index=True)
    beauty_title = Column(String, nullable=True)
    title = Column(String, nullable=False, index=True)
    other_titles = Column(String, nullable=True)
    connect = Column(Text, nullable=True)
    add_time = Column(DateTime, nullable=False)
    status = Column(Enum(PassStatus), nullable=False, default=PassStatus.new)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User", back_populates="passes")
    latitude = Column(String, nullable=False)
    longitude = Column(String, nullable=False)
    height = Column(String, nullable=True)
    level_winter = Column(String, nullable=True)
    level_summer = Column(String, nullable=True)
    level_autumn = Column(String, nullable=True)
    level_spring = Column(String, nullable=True)
    images = relationship("Image", back_populates="pass_", cascade="all, delete-orphan")

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    data = Column(Text, nullable=False)
    title = Column(String, nullable=True)
    pass_id = Column(Integer, ForeignKey("pass.id"), nullable=False)
    pass_ = relationship("Pass", back_populates="images")

# --------------------
# Pydantic модели
# --------------------
class ImageCreate(BaseModel):
    data: str
    title: str | None = None

class UserCreate(BaseModel):
    email: str
    fam: str
    name: str
    otc: str | None = None
    phone: str | None = None

class Coords(BaseModel):
    latitude: constr(strip_whitespace=True)
    longitude: constr(strip_whitespace=True)
    height: str | None = None

class Level(BaseModel):
    winter: str | None = None
    summer: str | None = None
    autumn: str | None = None
    spring: str | None = None

class PassCreate(BaseModel):
    beauty_title: str | None = None
    title: str
    other_titles: str | None = None
    connect: str | None = None
    add_time: datetime.datetime
    user: UserCreate
    coords: Coords
    level: Level
    images: list[ImageCreate] | None = None

class PassResponse(BaseModel):
    status: int
    message: str | None
    id: int | None

class PassDetailResponse(BaseModel):
    id: int
    beauty_title: str | None = None
    title: str
    other_titles: str | None = None
    connect: str | None = None
    add_time: datetime.datetime
    user: UserCreate
    coords: Coords
    level: Level
    images: list[ImageCreate] = []

# --------------------
# FastAPI приложение
# --------------------
app = FastAPI(title="FSTR Pass API", version="1.0")

# --------------------
# Сессия
# --------------------
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except:
            await session.rollback()
            raise

# --------------------
# Создание базы, если не существует
# --------------------
async def create_database_if_not_exists():
    conn = await asyncpg.connect(**ADMIN_DATABASE_URL)
    try:
        exists = await conn.fetchval('SELECT 1 FROM pg_database WHERE datname=$1', DB_NAME)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{DB_NAME}"')
    finally:
        await conn.close()

@app.on_event("startup")
async def on_startup():
    try:
        await create_database_if_not_exists()
    except Exception as e:
        print(f"Ошибка при создании базы данных: {e}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --------------------
# Эндпоинты
# --------------------
@app.get("/")
async def root():
    return {"message": "API is running"}

# POST /submitData
@app.post("/submitData", response_model=PassResponse)
async def submit_pass(data: PassCreate, session: AsyncSession = Depends(get_session)):
    if not data.title or not data.coords.latitude or not data.coords.longitude or not data.user.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Отсутствуют обязательные поля")
    try:
        result = await session.execute(select(User).where(User.email == data.user.email))
        user_obj = result.scalar_one_or_none()
        if user_obj is None:
            user_obj = User(
                email=data.user.email,
                fam=data.user.fam,
                name=data.user.name,
                otc=data.user.otc,
                phone=data.user.phone,
            )
            session.add(user_obj)
            await session.flush()  # Получаем id после добавления

        new_pass = Pass(
            beauty_title=data.beauty_title,
            title=data.title,
            other_titles=data.other_titles,
            connect=data.connect,
            add_time=data.add_time,
            status=PassStatus.new,
            user_id=user_obj.id,
            latitude=data.coords.latitude,
            longitude=data.coords.longitude,
            height=data.coords.height,
            level_winter=data.level.winter,
            level_summer=data.level.summer,
            level_autumn=data.level.autumn,
            level_spring=data.level.spring,
        )
        session.add(new_pass)
        await session.flush()

        if data.images:
            for img in data.images:
                image = Image(
                    data=img.data,
                    title=img.title,
                    pass_id=new_pass.id,
                )
                session.add(image)

        await session.commit()
        return PassResponse(status=200, message=None, id=new_pass.id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {e}")

# GET /submitData/{id} - получить запись по ID
@app.get("/submitData/{pass_id}", response_model=PassDetailResponse)
async def get_pass(pass_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Pass).where(Pass.id == pass_id))
    pass_obj = result.scalar_one_or_none()
    if pass_obj is None:
        raise HTTPException(status_code=404, detail="Перевал не найден")
    return PassDetailResponse(
        id=pass_obj.id,
        beauty_title=pass_obj.beauty_title,
        title=pass_obj.title,
        other_titles=pass_obj.other_titles,
        connect=pass_obj.connect,
        add_time=pass_obj.add_time,
        user=UserCreate(
            email=pass_obj.user.email,
            fam=pass_obj.user.fam,
            name=pass_obj.user.name,
            otc=pass_obj.user.otc,
            phone=pass_obj.user.phone
        ),
        coords=Coords(
            latitude=pass_obj.latitude,
            longitude=pass_obj.longitude,
            height=pass_obj.height
        ),
        level=Level(
            winter=pass_obj.level_winter,
            summer=pass_obj.level_summer,
            autumn=pass_obj.level_autumn,
            spring=pass_obj.level_spring
        ),
        images=[ImageCreate(data=img.data, title=img.title) for img in pass_obj.images]
    )

# PATCH /submitData/{id} - редактировать запись если status=new
@app.patch("/submitData/{pass_id}", response_model=PassResponse)
async def update_pass(pass_id: int, data: PassCreate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Pass).where(Pass.id == pass_id))
    pass_obj = result.scalar_one_or_none()
    if pass_obj is None:
        raise HTTPException(status_code=404, detail="Перевал не найден")
    if pass_obj.status != PassStatus.new:
        raise HTTPException(status_code=400, detail="Редактирование разрешено только для новых записей")
    try:
        pass_obj.beauty_title = data.beauty_title
        pass_obj.title = data.title
        pass_obj.other_titles = data.other_titles
        pass_obj.connect = data.connect
        pass_obj.add_time = data.add_time
        pass_obj.latitude = data.coords.latitude
        pass_obj.longitude = data.coords.longitude
        pass_obj.height = data.coords.height
        pass_obj.level_winter = data.level.winter
        pass_obj.level_summer = data.level.summer
        pass_obj.level_autumn = data.level.autumn
        pass_obj.level_spring = data.level.spring
        await session.commit()
        return PassResponse(status=200, message=None, id=pass_obj.id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {e}")

# GET /submitData/?user__email=<email> - получить все записи пользователя
@app.get("/submitData/", response_model=list[PassDetailResponse])
async def get_user_passes(user__email: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == user__email))
    user_obj = result.scalar_one_or_none()
    if user_obj is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    passes = [
        PassDetailResponse(
            id=p.id,
            beauty_title=p.beauty_title,
            title=p.title,
            other_titles=p.other_titles,
            connect=p.connect,
            add_time=p.add_time,
            user=UserCreate(
                email=user_obj.email,
                fam=user_obj.fam,
                name=user_obj.name,
                otc=user_obj.otc,
                phone=user_obj.phone
            ),
            coords=Coords(
                latitude=p.latitude,
                longitude=p.longitude,
                height=p.height
            ),
            level=Level(
                winter=p.level_winter,
                summer=p.level_summer,
                autumn=p.level_autumn,
                spring=p.level_spring
            ),
            images=[ImageCreate(data=img.data, title=img.title) for img in p.images]
        ) for p in user_obj.passes
    ]
    return passes
