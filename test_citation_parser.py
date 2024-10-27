from toolkit.parsers.citation import CitationParser

def test_parse_citations():
    # Test data covering all formats from actual TLG files
    test_lines = [
        "[0627][050][][]",  # TLG reference
        ".t.1 {ΠΕΡΙ ΕΥΣΧΗΜΟΣΥΝΗΣ.}",  # Title line
        ".1.1 Οὐκ ἀλόγως οἱ προβαλλόμενοι",  # Chapter.line
        ".1.2 χρησίμην, ταύτην δὴ τὴν ἐν τῷ βίῳ.",  # Another chapter.line
        ".847a.t. <ΜΗΧΑΝΙΚΑ.>",  # Section with title
        ".847a.11 Θαυμάζεται τῶν μὲν",  # Section with line
        ".1 Ὄμνυμι Ἀπόλλωνα ἰητρὸν",  # Single section
        "Some text without citation"  # No citation
    ]

    parser = CitationParser()
    
    print("Testing citation parsing...")
    for line in test_lines:
        remaining, citations = parser.parse_citation(line)
        print(f"\nInput: {line}")
        print(f"Remaining: {remaining}")
        if citations:
            for citation in citations:
                print(f"Citation object:")
                print(f"  Raw citation: {citation.raw_citation}")
                if citation.author_id:
                    print(f"  Author ID: {citation.author_id}")
                if citation.work_id:
                    print(f"  Work ID: {citation.work_id}")
                if citation.division:
                    print(f"  Division: {citation.division}")
                if citation.subdivision:
                    print(f"  Subdivision: {citation.subdivision}")
                if citation.title_number:
                    print(f"  Title number: {citation.title_number}")
                if citation.section:
                    print(f"  Section: {citation.section}")
                if citation.subsection:
                    print(f"  Subsection: {citation.subsection}")
                if citation.chapter:
                    print(f"  Chapter: {citation.chapter}")
                if citation.line:
                    print(f"  Line: {citation.line}")
                print(f"  String representation: {str(citation)}")

if __name__ == "__main__":
    test_parse_citations()
