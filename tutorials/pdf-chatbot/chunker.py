from pypdf import PdfReader
import re
from typing import List

class PDFChunker:
    def __init__(self, chunk_size: int = 1000, overlap_size: int = 200):
        """
        Initialize the PDF chunker with configurable parameters.
        
        Args:
            chunk_size: Target size for each chunk in characters
            overlap_size: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a single string
        """
        try:
            reader = PdfReader(pdf_path)
            context = "\n".join([page.extract_text() for page in reader.pages])
            return context
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
    
    def clean_text(self, text: str) -> str:
        """
        Clean the extracted text by normalizing whitespace and removing artifacts.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace and normalize line breaks
        text = re.sub(r'\s+', ' ', text)
        # Remove common PDF artifacts
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/\@\#\$\%\&\*\+\=\<\>\~\`\|\\]', '', text)
        return text.strip()
    
    def chunk_by_words(self, text: str) -> List[str]:
        """
        Chunk text using word-based overlapping strategy.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks with word overlap
        """
        words = text.split()
        if not words:
            return []
        
        chunks = []
        start_idx = 0
        
        while start_idx < len(words):
            # Calculate end index for current chunk
            end_idx = start_idx + self._words_in_chunk(words[start_idx:])
            end_idx = min(end_idx, len(words))
            
            # Create chunk from words
            chunk = ' '.join(words[start_idx:end_idx])
            chunks.append(chunk)
            
            # If we've reached the end, break
            if end_idx >= len(words):
                break
            
            # Calculate overlap for next chunk
            overlap_words = self._words_in_overlap(words[start_idx:end_idx])
            start_idx = max(start_idx + 1, end_idx - overlap_words)
        
        return chunks
    
    def _words_in_chunk(self, words: List[str]) -> int:
        """
        Calculate how many words fit in a chunk of target character size.
        """
        char_count = 0
        word_count = 0
        
        for word in words:
            # Add word length plus space
            word_len = len(word) + 1
            if char_count + word_len > self.chunk_size and word_count > 0:
                break
            char_count += word_len
            word_count += 1
        
        return max(1, word_count)  # Ensure at least one word per chunk
    
    def _words_in_overlap(self, words: List[str]) -> int:
        """
        Calculate how many words to include in overlap.
        """
        char_count = 0
        word_count = 0
        
        # Count words from the end backwards
        for word in reversed(words):
            word_len = len(word) + 1
            if char_count + word_len > self.overlap_size:
                break
            char_count += word_len
            word_count += 1
        
        return word_count
    
    def process_pdf(self, pdf_path: str) -> List[str]:
        """
        Complete pipeline to extract and chunk PDF content.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of text chunks
        """
        # Extract text
        raw_text = self.extract_text_from_pdf(pdf_path)
        if not raw_text:
            return []
        
        # Clean text
        cleaned_text = self.clean_text(raw_text)
        
        # Chunk text
        return self.chunk_by_words(cleaned_text)
    
    def print_chunk_stats(self, chunks: List[str]) -> None:
        """
        Print statistics about the chunks.
        """
        if not chunks:
            print("No chunks generated.")
            return
        
        chunk_lengths = [len(chunk) for chunk in chunks]
        
        print(f"Total chunks: {len(chunks)}")
        print(f"Average chunk length: {sum(chunk_lengths) / len(chunk_lengths):.0f} characters")
        print(f"Min chunk length: {min(chunk_lengths)} characters")
        print(f"Max chunk length: {max(chunk_lengths)} characters")
        
        # Show overlap analysis
        if len(chunks) > 1:
            overlaps = []
            for i in range(len(chunks) - 1):
                overlap = self._calculate_overlap(chunks[i], chunks[i + 1])
                overlaps.append(overlap)
            
            if overlaps:
                avg_overlap = sum(overlaps) / len(overlaps)
                print(f"Average overlap: {avg_overlap:.0f} characters")
    
    def _calculate_overlap(self, chunk1: str, chunk2: str) -> int:
        """
        Calculate the character overlap between two chunks.
        """
        # Find the longest common suffix of chunk1 and prefix of chunk2
        max_overlap = min(len(chunk1), len(chunk2))
        
        for i in range(max_overlap, 0, -1):
            if chunk1.endswith(chunk2[:i]):
                return i
        
        return 0