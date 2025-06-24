# main.py
import uvicorn
from fastapi import FastAPI
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel,ConfigDict
from typing import List
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

# --- Database setup ---
DATABASE_URL = "sqlite:///./library.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# --- Models ---
class AuthorModel(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    books = relationship("BookModel", back_populates="author", cascade="all, delete")

class BookModel(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author_id = Column(Integer, ForeignKey("authors.id"))
    isbn = Column(String, unique=True, index=True)
    copies_available = Column(Integer, default=0)
    author = relationship("AuthorModel", back_populates="books")

Base.metadata.create_all(bind=engine)

# --- Schemas ---
class Author(BaseModel):
    id: int
    name: str
    class Config:
        model_config=ConfigDict(from_attributes=True)

class AuthorCreate(BaseModel):
    name: str

class Book(BaseModel):
    id: int
    title: str
    author_id: int
    isbn: str
    copies_available: int
    class Config:
        model_config=ConfigDict(from_attributes=True)

class BookCreate(BaseModel):
    title: str
    author_id: int
    isbn: str
    copies_available: int = 1

# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- App initialization ---
app = FastAPI(title="Library Inventory API")

# --- Author Endpoints ---
@app.post("/authors/", response_model=Author, status_code=201)
def create_author(author: AuthorCreate, db: Session = Depends(get_db)):
    db_author = AuthorModel(**author.dict())
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author

@app.get("/authors/", response_model=List[Author])
def get_authors(db: Session = Depends(get_db)):
    return db.query(AuthorModel).all()

@app.get("/authors/{author_id}", response_model=Author)
def get_author(author_id: int, db: Session = Depends(get_db)):
    author = db.get(AuthorModel, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author

@app.delete("/authors/{author_id}", status_code=204)
def delete_author(author_id: int, db: Session = Depends(get_db)):
    author = db.get(AuthorModel, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    db.delete(author)
    db.commit()

# --- Book Endpoints ---
@app.post("/books/", response_model=Book, status_code=201)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    if not db.get(AuthorModel, book.author_id):
        raise HTTPException(status_code=400, detail="Invalid author_id")
    db_book = BookModel(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.get("/books/", response_model=List[Book])
def get_books(db: Session = Depends(get_db)):
    return db.query(BookModel).all()

@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(BookModel, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.put("/books/{book_id}", response_model=Book)
def update_book(book_id: int, book: BookCreate, db: Session = Depends(get_db)):
    db_book = db.get(BookModel, book_id)
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    for attr, value in book.dict().items():
        setattr(db_book, attr, value)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(BookModel, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
def main():
    print("Hello world")
    import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,
        reload=True  # only if needed during development
    )


