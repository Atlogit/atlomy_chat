"""
Example usage of the text processing toolkit's parser modules.

This module demonstrates how to use the citation, text, and sentence parsers
together to process ancient medical texts while maintaining structure and citations.
"""

import asyncio
from pathlib import Path
from typing import List

from .citation import CitationParser
from .text import TextParser, TextLine
from .sentence import SentenceParser, Sentence
from .exceptions import ParsingError

async def process_text_file(file_path: Path) -> List[Sentence]:
    """Process a text file through the complete parsing pipeline.
    
    This example shows how to:
    1. Parse text into lines with citations
    2. Convert lines into sentences while maintaining references
    
    Args:
        file_path: Path to the text file to process
        
    Returns:
        List of parsed sentences with citation information
        
    Example:
        For a file containing:
        [0057][001][1][2] First sentence. Second sentence.
        128.32.5 Third sentence continues
        and ends here.
        
        The function will return structured sentences with:
        - Complete sentence text
        - References to source lines
        - Associated citations
    """
    # Initialize parsers
    text_parser = TextParser()
    sentence_parser = SentenceParser()
    
    try:
        # Step 1: Parse text into lines with citations
        lines = await text_parser.parse_file(file_path)
        
        # Step 2: Convert lines into sentences
        sentences = await sentence_parser.parse_lines(lines)
        
        return sentences
        
    except ParsingError as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return []

async def analyze_citations(sentences: List[Sentence]) -> dict:
    """Analyze citation patterns in the parsed sentences.
    
    Args:
        sentences: List of parsed sentences
        
    Returns:
        Dictionary containing citation statistics
    """
    stats = {
        'total_sentences': len(sentences),
        'citations_per_sentence': [],
        'unique_authors': set(),
        'citation_types': {
            'tlg': 0,  # [0057][001][1][2] format
            'volume': 0,  # 128.32.5 format
            'title': 0  # .t.1 format
        }
    }
    
    sentence_parser = SentenceParser()
    
    for sentence in sentences:
        # Get all citations for this sentence
        citations = sentence_parser.get_sentence_citations(sentence)
        stats['citations_per_sentence'].append(len(citations))
        
        for citation in citations:
            # Track unique authors
            if citation.author_id:
                stats['unique_authors'].add(citation.author_id)
                stats['citation_types']['tlg'] += 1
            # Track volume references
            elif citation.volume:
                stats['citation_types']['volume'] += 1
            # Track title references
            elif citation.title_number:
                stats['citation_types']['title'] += 1
    
    # Calculate averages
    stats['avg_citations_per_sentence'] = (
        sum(stats['citations_per_sentence']) / len(sentences)
        if sentences else 0
    )
    stats['unique_authors'] = len(stats['unique_authors'])
    
    return stats

def print_sentence_analysis(sentence: Sentence, sentence_parser: SentenceParser):
    """Print detailed analysis of a parsed sentence."""
    print("\nSentence Analysis:")
    print("-" * 50)
    print(f"Content: {sentence.content}")
    print("\nSource Lines:")
    for line in sentence.source_lines:
        print(f"  - {line.content}")
    
    print("\nCitations:")
    citations = sentence_parser.get_sentence_citations(sentence)
    for citation in citations:
        print(f"  - {str(citation)}")
    
    print("\nPosition:")
    print(f"  Start: {sentence.start_position}")
    print(f"  End: {sentence.end_position}")
    print("-" * 50)

async def main():
    """Example usage of the parsing pipeline."""
    # Example text file path
    file_path = Path("example.txt")
    
    # Create example content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("""[0057][001][1][2] First sentence about τὸ σῶμα. Second sentence here.
128.32.5 Third sentence continues
and ends here· Fourth sentence.
[0058][002][1][1] New section starts.""")
    
    try:
        # Process the file
        sentences = await process_text_file(file_path)
        
        # Print each sentence with its analysis
        sentence_parser = SentenceParser()
        for i, sentence in enumerate(sentences, 1):
            print(f"\nSentence {i}:")
            print_sentence_analysis(sentence, sentence_parser)
        
        # Analyze citation patterns
        stats = await analyze_citations(sentences)
        
        print("\nCitation Analysis:")
        print("-" * 50)
        print(f"Total Sentences: {stats['total_sentences']}")
        print(f"Average Citations per Sentence: {stats['avg_citations_per_sentence']:.2f}")
        print(f"Unique Authors: {stats['unique_authors']}")
        print("\nCitation Types:")
        for type_name, count in stats['citation_types'].items():
            print(f"  {type_name}: {count}")
            
    finally:
        # Cleanup example file
        file_path.unlink()

if __name__ == "__main__":
    asyncio.run(main())
