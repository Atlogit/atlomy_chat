"""Script to view migrated texts and lines from the database."""
import asyncio
from app.core.database import async_session
from app.services.corpus_service import CorpusService

async def view_texts():
    """View all texts and their lines in the database."""
    async with async_session() as session:
        service = CorpusService(session)
        
        # List all texts
        texts = await service.list_texts()
        print("\n=== All Texts ===")
        for text in texts:
            print(f"\nTitle: {text['title']}")
            print(f"Author: {text['author']}")
            print(f"Reference: {text['reference_code']}")
            
            # Get full text content with lines
            text_content = await service.get_text_by_id(int(text['id']))
            if text_content and text_content['divisions']:
                print("\nContent:")
                for division in text_content['divisions']:
                    for line in division['lines']:
                        print(f"{line['line_number']}: {line['content']}")
            print("-" * 80)

if __name__ == "__main__":
    asyncio.run(view_texts())
