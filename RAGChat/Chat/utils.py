import os
import logging
import pickle
from pathlib import Path
from django.conf import settings
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from .models import PDFDocument, DocumentChunk



logger = logging.getLogger(__name__)


class TFIDFVectorStore:
    def __init__(self, persist_directory=None, load_existing=True):
        self.persist_directory = persist_directory
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.documents = []
        self.vectors = None

        if load_existing and persist_directory and Path(persist_directory).exists():
            vectorizer_path = Path(persist_directory) / 'vectorizer.pkl'
            if vectorizer_path.exists():
                self.load()

    def add_texts(self, texts):
        self.documents = texts
        self.vectors = self.vectorizer.fit_transform(texts)
        return self

    def similarity_search(self, query, k=4):
        if not self.documents:
            return []

        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.vectors)[0]

        top_indices = np.argsort(similarities)[-k:][::-1]

        class Document:
            def __init__(self, content):
                self.page_content = content

        return [Document(self.documents[i]) for i in top_indices]

    def persist(self):
        if not self.persist_directory:
            return

        persist_path = Path(self.persist_directory)
        persist_path.mkdir(parents=True, exist_ok=True)

        with open(persist_path / 'vectorizer.pkl', 'wb') as f:
            pickle.dump(self.vectorizer, f)

        with open(persist_path / 'documents.pkl', 'wb') as f:
            pickle.dump(self.documents, f)

        logger.info(f"Vector store saved to {persist_path}")

    def load(self):
        persist_path = Path(self.persist_directory)

        try:
            with open(persist_path / 'vectorizer.pkl', 'rb') as f:
                self.vectorizer = pickle.load(f)

            with open(persist_path / 'documents.pkl', 'rb') as f:
                self.documents = pickle.load(f)

            if self.documents:
                self.vectors = self.vectorizer.transform(self.documents)

            logger.info(f"Vector store loaded from {persist_path}")
        except Exception as e:
            logger.error(f"Failed to load vector store: {str(e)}")
            raise


class PDFProcessor:
    def __init__(self, document):
        self.document = document

    def extract_text(self):
        try:
            loader = PyPDFLoader(self.document.pdf_file.path)
            pages = loader.load()

            if not pages:
                raise Exception("PDF is empty or cannot be read")

            return pages

        except Exception as e:
            logger.error(f"PDF extraction failed for {self.document.id}: {str(e)}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")

    def chunk_text(self, pages, chunk_size=1000, chunk_overlap=200):
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )

            chunks = text_splitter.split_documents(pages)

            for i, chunk in enumerate(chunks):
                DocumentChunk.objects.create(
                    document=self.document,
                    text=chunk.page_content,
                )

            return [chunk.page_content for chunk in chunks]

        except Exception as e:
            logger.error(f"Text chunking failed: {str(e)}")
            raise Exception(f"Failed to chunk text: {str(e)}")

    def create_vector_store(self, chunks):
        try:
            vector_dir = Path(settings.MEDIA_ROOT) / 'vector_stores' / str(self.document.user.id) / str(
                self.document.id)
            vector_dir.mkdir(parents=True, exist_ok=True)

            vectordb = TFIDFVectorStore(persist_directory=str(vector_dir), load_existing=False)
            vectordb.add_texts(chunks)
            vectordb.persist()

            logger.info(f"Vector store created for document {self.document.id}")
            return True

        except Exception as e:
            logger.error(f"Vector store creation failed: {str(e)}")
            raise Exception(f"Failed to create vector store: {str(e)}")


class RAGService:
    def __init__(self, user, document_id=None):
        self.user = user
        self.document_id = document_id

    def get_vector_store(self):
        try:
            if self.document_id:
                document = PDFDocument.objects.get(id=self.document_id, user=self.user)
                vector_path = Path(settings.MEDIA_ROOT) / 'vector_stores' / str(self.user.id) / str(document.id)
            else:
                vector_path = Path(settings.MEDIA_ROOT) / 'vector_stores' / str(self.user.id)
                first_doc = PDFDocument.objects.filter(user=self.user).first()
                if first_doc:
                    vector_path = vector_path / str(first_doc.id)

            if not vector_path.exists():
                raise Exception("Vector store not found. Please upload and process the document first.")

            vectorizer_path = vector_path / 'vectorizer.pkl'
            if not vectorizer_path.exists():
                raise Exception("Vector store files not found. Please re-process the document.")

            return TFIDFVectorStore(persist_directory=str(vector_path), load_existing=True)

        except PDFDocument.DoesNotExist:
            raise Exception("Document not found or access denied")
        except Exception as e:
            logger.error(f"Failed to load vector store: {str(e)}")
            raise Exception(f"Failed to load vector store: {str(e)}")

    def search(self, query, k=4):
        """Search for relevant chunks"""
        try:
            vectordb = self.get_vector_store()
            results = vectordb.similarity_search(query, k=k)

            return [
                {
                    'content': doc.page_content,
                }
                for doc in results
            ]

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise Exception(f"Search failed: {str(e)}")


class LLMService:

    def __init__(self, model_name=None):
        if not hasattr(settings, 'GROQ_API_KEY') or not settings.GROQ_API_KEY:
            raise Exception("Groq API key not configured")

        self.model_name = model_name or getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')

    def generate_response(self, query, context):
        try:
            llm = ChatGroq(
                model=self.model_name,
                temperature=0.7,
                groq_api_key=settings.GROQ_API_KEY,
            )

            system_prompt = """You are a helpful assistant that answers questions based on the provided context.
            Context comes from user-uploaded PDF documents.

            Guidelines:
            1. If the context doesn't contain relevant information, say "I cannot find this information in the provided documents" answer normally
            2. Be concise and accurate
            3. Cite page numbers when available
            4. If asked about multiple topics, organize the answer clearly

            Context:
            {context}"""

            messages = [
                SystemMessage(content=system_prompt.format(context="/n/n".join(context))),
            ]

            messages.append(HumanMessage(content=query))

            response = llm.invoke(messages)

            return response.content

        except Exception as e:
            error_msg = str(e)
            logger.error(f"LLM generation failed: {error_msg}")
            raise Exception(f"Failed to generate response: {error_msg}")