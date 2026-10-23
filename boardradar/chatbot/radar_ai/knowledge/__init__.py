"""Local lexical evidence, without generation or external inference."""
from .index import DocumentIndex, load_index
from .answers import answer_query, is_document_query

__all__=['DocumentIndex','load_index','answer_query','is_document_query']
