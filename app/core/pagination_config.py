from typing import Optional, TypedDict

class PaginationConfig:
    """Centralized pagination configuration for the application."""
    
    # Default page sizes for different contexts
    DEFAULT_PAGE_SIZES = {
        'citations': 20,
        'lexical_entries': 20,
        'search_results': 20,
        'default': 10
    }
    
    @classmethod
    def get_page_size(cls, context: str = 'default') -> int:
        """
        Get page size for a specific context.
        
        Args:
            context: The context for which to retrieve page size
        
        Returns:
            Configured page size or default
        """
        return cls.DEFAULT_PAGE_SIZES.get(context, cls.DEFAULT_PAGE_SIZES['default'])
    
    @classmethod
    def set_page_size(cls, context: str, size: int):
        """
        Set page size for a specific context.
        
        Args:
            context: The context to configure
            size: New page size
        """
        cls.DEFAULT_PAGE_SIZES[context] = size

class PaginationParams(TypedDict, total=False):
    """Standardized pagination parameters."""
    page: int
    page_size: int
    total_results: Optional[int]
    total_pages: Optional[int]
