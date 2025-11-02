"""
EAF Document Acquisition System
Simple scraper for finding and downloading EAF documents from coordinador.cl
"""

from .eaf_document_finder import EAFDocumentFinder
from .eaf_downloader import EAFDownloader
from .document_validator import DocumentValidator

__all__ = ['EAFDocumentFinder', 'EAFDownloader', 'DocumentValidator']