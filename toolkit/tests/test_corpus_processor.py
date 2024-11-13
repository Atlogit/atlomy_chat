"""Test cases for corpus processing functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, call
from sqlalchemy.ext.asyncio import AsyncSession
from toolkit.migration.corpus_processor import CorpusProcessor
from app.models.text_line import TextLine
from app.models.text_division import TextDivision
from toolkit.parsers.text import TextLine as ParserTextLine
from toolkit.parsers.citation import Citation
from toolkit.parsers.sentence import Sentence
from datetime import datetime

@pytest.fixture
def mock_session():
    """Create a mock SQLAlchemy session."""
    session = AsyncMock(spec=AsyncSession)
    session.add = Mock()  # Use sync mock for add since we just track calls
    session.flush = AsyncMock()  # Use async mock for flush since we await it
    return session

@pytest.fixture
def processor(mock_session):
    """Create a CorpusProcessor instance with mocked dependencies."""
    processor = CorpusProcessor(session=mock_session)
    # Mock methods we need from parent classes
    processor._convert_to_parser_text_line = Mock()
    processor._get_sentence_lines = Mock()
    processor._process_doc_to_dict = Mock()
    processor.sentence_parser = Mock()
    return processor

def test_get_citation_line_number_with_section_line_structure(processor):
    """Test line number extraction for Section.Line structure."""
    # Mock TLG_WORKS_INDEX and TLG_MASTER_INDEX
    mock_works_index = {
        "0627": {"010": "De Articulis"}
    }
    mock_master_index = {
        "hippocrates": {
            "tlg_id": "TLG0627",
            "works": {
                "De Articulis": ["Section", "Line"]  # Fixed string concatenation
            }
        }
    }
    
    division = TextDivision(
        author_id_field="0627",
        work_number_field="010",
        chapter="1"
    )
    
    with patch('assets.indexes.work_numbers.TLG_WORKS_INDEX', mock_works_index), \
         patch('assets.indexes.tlg_index.TLG_MASTER_INDEX', mock_master_index):
        # Title line
        assert processor._get_citation_line_number(".t.1 {ΠΕΡΙ ΑΡΘΡΩΝ.}", division) == 1
        
        # Regular lines with Section.Line structure
        assert processor._get_citation_line_number(".1.5 First line", division) == 5
        assert processor._get_citation_line_number(".2.10 Second line", division) == 10
        
        # Invalid content
        assert processor._get_citation_line_number("No citation here", division) is None
        assert processor._get_citation_line_number("", division) is None
        assert processor._get_citation_line_number(None, division) is None

def test_get_citation_line_number_with_alphanumeric_levels(processor):
    """Test line number extraction with alphanumeric level values."""
    # Mock TLG_WORKS_INDEX and TLG_MASTER_INDEX
    mock_works_index = {
        "0086": {"001": "Test Work"}
    }
    mock_master_index = {
        "author": {
            "tlg_id": "TLG0086",
            "works": {
                "Test Work": ["Book", "Chapter", "Line"]  # Fixed string concatenation
            }
        }
    }
    
    division = TextDivision(
        author_id_field="0086",
        work_number_field="001",
        chapter="653a"
    )
    
    with patch('assets.indexes.work_numbers.TLG_WORKS_INDEX', mock_works_index), \
         patch('assets.indexes.tlg_index.TLG_MASTER_INDEX', mock_master_index):
        # Lines with alphanumeric level values
        assert processor._get_citation_line_number(".4.653a.10 First line", division) == 10
        assert processor._get_citation_line_number(".4.653b.15 Second line", division) == 15
        
        # Complex citations
        assert processor._get_citation_line_number(".4.653a.10a Some text", division) == 10
        assert processor._get_citation_line_number(".4a.653.20 Some text", division) == 20

def test_adjust_line_numbers_with_section_line_structure(processor):
    """Test line number adjustment for Section.Line structure."""
    # Mock TLG_WORKS_INDEX and TLG_MASTER_INDEX
    mock_works_index = {
        "0627": {"010": "De Articulis"}
    }
    mock_master_index = {
        "hippocrates": {
            "tlg_id": "TLG0627",
            "works": {
                "De Articulis": ["Section", "Line"]  # Fixed string concatenation
            }
        }
    }
    
    division = TextDivision(
        author_id_field="0627",
        work_number_field="010",
        chapter="1"
    )
    
    db_lines = [
        TextLine(
            content=".t.1 {ΠΕΡΙ ΑΡΘΡΩΝ.}",
            line_number=1
        ),
        TextLine(
            content=".1.5 First line of section one",
            line_number=2
        ),
        TextLine(
            content=".1.6 Second line of section one",
            line_number=3
        )
    ]
    
    with patch('assets.indexes.work_numbers.TLG_WORKS_INDEX', mock_works_index), \
         patch('assets.indexes.tlg_index.TLG_MASTER_INDEX', mock_master_index):
        parser_lines, line_map = processor._adjust_line_numbers(db_lines, division)
        
        assert len(parser_lines) == 3
        # Title line gets number from citation
        assert parser_lines[0].line_number == 1
        assert parser_lines[0].is_title == True
        # Content lines get numbers from citations
        assert parser_lines[1].line_number == 5
        assert parser_lines[1].is_title == False
        assert parser_lines[2].line_number == 6
        assert parser_lines[2].is_title == False
        
        # Verify line mapping
        assert line_map[5].content == ".1.5 First line of section one"
        assert line_map[6].content == ".1.6 Second line of section one"

def test_adjust_line_numbers_with_alphanumeric_levels(processor):
    """Test line number adjustment with alphanumeric level values."""
    # Mock TLG_WORKS_INDEX and TLG_MASTER_INDEX
    mock_works_index = {
        "0086": {"001": "Test Work"}
    }
    mock_master_index = {
        "author": {
            "tlg_id": "TLG0086",
            "works": {
                "Test Work": ["Book", "Chapter", "Line"]  # Fixed string concatenation
            }
        }
    }
    
    division = TextDivision(
        author_id_field="0086",
        work_number_field="001",
        chapter="653a"
    )
    
    db_lines = [
        TextLine(
            content=".4.653a.10 First line",
            line_number=1
        ),
        TextLine(
            content=".4.653a.11 Second line",
            line_number=2
        )
    ]
    
    with patch('assets.indexes.work_numbers.TLG_WORKS_INDEX', mock_works_index), \
         patch('assets.indexes.tlg_index.TLG_MASTER_INDEX', mock_master_index):
        parser_lines, line_map = processor._adjust_line_numbers(db_lines, division)
        
        assert len(parser_lines) == 2
        # Lines get numbers from citations
        assert parser_lines[0].line_number == 10
        assert parser_lines[0].is_title == False
        assert parser_lines[1].line_number == 11
        assert parser_lines[1].is_title == False
        
        # Verify line mapping
        assert line_map[10].content == ".4.653a.10 First line"
        assert line_map[11].content == ".4.653a.11 Second line"

@pytest.mark.asyncio
async def test_process_work_with_section_line_structure(processor):
    """Test processing of work with Section.Line structure."""
    # Mock TLG_WORKS_INDEX and TLG_MASTER_INDEX
    mock_works_index = {
        "0627": {"010": "De Articulis"}
    }
    mock_master_index = {
        "hippocrates": {
            "tlg_id": "TLG0627",
            "works": {
                "De Articulis": ["Section", "Line"]  # Fixed string concatenation
            }
        }
    }
    
    # Mock the database queries
    mock_text = Mock(id=1)
    mock_division = Mock(
        id=1,
        chapter="1",
        author_id_field="0627",
        work_number_field="010"
    )
    
    # Create mock lines with citations
    mock_lines = []
    for line_data in [
        (1, ".t.1 {ΠΕΡΙ ΑΡΘΡΩΝ.}", 1, True),
        (2, ".1.5 First line of section one", 5, False),
        (3, ".1.6 Second line of section one.", 6, False)
    ]:
        line_id, content, line_num, is_title = line_data
        citation = Citation(
            author_id="0627",
            work_id="010",
            hierarchy_levels={"section": "1", "line": str(line_num)}
        )
        line = TextLine(
            id=line_id,
            content=content,
            line_number=line_num
        )
        line.citation = citation
        line.is_title = is_title
        mock_lines.append(line)
    
    # Mock spaCy pipeline
    mock_nlp = Mock()
    mock_doc = Mock()
    mock_doc.text = "First line of section one Second line of section one."
    mock_doc.tokens = []
    mock_nlp.return_value = mock_doc
    processor.nlp_pipeline = Mock()
    processor.nlp_pipeline.nlp = mock_nlp
    
    # Mock sentence parser
    mock_sentence = Sentence(
        content="First line of section one Second line of section one.",
        source_lines=mock_lines[1:],  # Exclude title line
        citation=mock_lines[1].citation  # Use citation from first content line
    )
    processor.sentence_parser.parse_lines = Mock(return_value=[mock_sentence])
    
    # Mock _convert_to_parser_text_line to return the lines with citations
    def convert_line(line, division):
        parser_line = ParserTextLine(
            content=line.content,
            citation=line.citation,
            is_title=line.is_title,
            line_number=line.line_number
        )
        return parser_line
    processor._convert_to_parser_text_line.side_effect = convert_line
    
    # Mock _get_sentence_lines to return the correct lines
    processor._get_sentence_lines.return_value = mock_lines[1:]  # Return content lines
    
    # Mock _process_doc_to_dict to return a valid doc dict
    processed_doc = {
        "text": mock_doc.text,
        "tokens": []
    }
    processor._process_doc_to_dict.return_value = processed_doc
    
    # Set up mock query results
    processor.session.execute = AsyncMock()
    processor.session.execute.side_effect = [
        Mock(scalar_one=lambda: mock_text),  # For Text query
        Mock(scalars=lambda: Mock(all=lambda: [mock_division])),  # For TextDivision query
        Mock(scalars=lambda: Mock(all=lambda: mock_lines))  # For TextLine query
    ]
    
    with patch('assets.indexes.work_numbers.TLG_WORKS_INDEX', mock_works_index), \
         patch('assets.indexes.tlg_index.TLG_MASTER_INDEX', mock_master_index):
        try:
            # Process the work
            await processor.process_work(1)
            
            # Verify database operations
            add_calls = [
                call for call in processor.session.add.call_args_list
                if call[0][0].__class__.__name__ == 'Sentence'
            ]
            
            # Check sentence creation
            assert len(add_calls) == 1  # One sentence from the content lines
            created_sentence = add_calls[0][0][0]
            
            # Verify source line IDs use database IDs but correspond to correct citation numbers
            assert created_sentence.source_line_ids == [2, 3]  # Database IDs for lines .1.5 and .1.6
            
            # Verify sentence content
            assert created_sentence.content == processed_doc["text"]
            assert created_sentence.spacy_data == processed_doc
            assert created_sentence.categories == []
            
            # Verify session.add and flush were called
            assert processor.session.add.call_count > 0
            assert processor.session.flush.call_count > 0
            
        except Exception as e:
            pytest.fail(f"Test failed with error: {str(e)}")  # Show the actual error
