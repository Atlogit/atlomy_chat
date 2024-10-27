"""
Unit tests for the LexicalService.
Tests lemma operations and analysis management.
"""

import pytest
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import LexicalService
from app.models.lemma import Lemma
from app.models.lemma_analysis import LemmaAnalysis
from tests.fixtures import (
    db_session,
    sample_lemma,
    sample_analysis
)

@pytest.mark.asyncio
async def test_create_lemma(
    db_session: AsyncSession
) -> None:
    """Test creating a new lemma."""
    service = LexicalService(db_session)
    
    # Test creating new lemma
    result = await service.create_lemma(
        lemma="θεραπεία",
        language_code="grc",
        categories=["medical", "treatment"],
        translations={
            "en": "treatment, cure",
            "de": "Behandlung"
        }
    )
    
    assert result["success"] is True
    assert result["action"] == "create"
    assert result["entry"]["lemma"] == "θεραπεία"
    assert "medical" in result["entry"]["categories"]
    assert result["entry"]["translations"]["en"] == "treatment, cure"
    
    # Test duplicate lemma
    result = await service.create_lemma(
        lemma="θεραπεία",
        language_code="grc"
    )
    
    assert result["success"] is False
    assert result["action"] == "update"
    assert result["message"] == "Lemma already exists"

@pytest.mark.asyncio
async def test_get_lemma(
    db_session: AsyncSession,
    sample_lemma: Lemma
) -> None:
    """Test retrieving a lemma."""
    service = LexicalService(db_session)
    
    # Test existing lemma
    lemma = await service.get_lemma_by_text(sample_lemma.lemma)
    assert lemma is not None
    assert lemma.lemma == "νόσος"
    assert lemma.language_code == "grc"
    assert "medical" in lemma.categories
    
    # Test nonexistent lemma
    lemma = await service.get_lemma_by_text("nonexistent")
    assert lemma is None

@pytest.mark.asyncio
async def test_list_lemmas(
    db_session: AsyncSession,
    sample_lemma: Lemma
) -> None:
    """Test listing lemmas with filters."""
    service = LexicalService(db_session)
    
    # Test listing all lemmas
    lemmas = await service.list_lemmas()
    assert len(lemmas) == 1
    assert lemmas[0]["lemma"] == "νόσος"
    
    # Test filtering by language
    lemmas = await service.list_lemmas(language_code="grc")
    assert len(lemmas) == 1
    
    lemmas = await service.list_lemmas(language_code="lat")
    assert len(lemmas) == 0
    
    # Test filtering by category
    lemmas = await service.list_lemmas(category="medical")
    assert len(lemmas) == 1
    
    lemmas = await service.list_lemmas(category="nonexistent")
    assert len(lemmas) == 0

@pytest.mark.asyncio
async def test_update_lemma(
    db_session: AsyncSession,
    sample_lemma: Lemma
) -> None:
    """Test updating a lemma."""
    service = LexicalService(db_session)
    
    # Update translations
    result = await service.update_lemma(
        lemma="νόσος",
        translations={
            "en": "disease, sickness, plague",
            "fr": "maladie"
        }
    )
    
    assert result["success"] is True
    assert result["entry"]["translations"]["en"] == "disease, sickness, plague"
    assert result["entry"]["translations"]["fr"] == "maladie"
    
    # Update categories
    result = await service.update_lemma(
        lemma="νόσος",
        categories=["medical", "disease", "pathology"]
    )
    
    assert result["success"] is True
    assert "pathology" in result["entry"]["categories"]
    
    # Test updating nonexistent lemma
    result = await service.update_lemma(
        lemma="nonexistent",
        translations={"en": "test"}
    )
    
    assert result["success"] is False
    assert result["message"] == "Lemma not found"

@pytest.mark.asyncio
async def test_delete_lemma(
    db_session: AsyncSession,
    sample_lemma: Lemma
) -> None:
    """Test deleting a lemma."""
    service = LexicalService(db_session)
    
    # Test deleting existing lemma
    success = await service.delete_lemma("νόσος")
    assert success is True
    
    # Verify deletion
    lemma = await service.get_lemma_by_text("νόσος")
    assert lemma is None
    
    # Test deleting nonexistent lemma
    success = await service.delete_lemma("nonexistent")
    assert success is False

@pytest.mark.asyncio
async def test_lemma_analysis(
    db_session: AsyncSession,
    sample_lemma: Lemma
) -> None:
    """Test creating and retrieving lemma analyses."""
    service = LexicalService(db_session)
    
    # Create analysis
    result = await service.create_analysis(
        lemma="νόσος",
        analysis_text="Analysis of the term νόσος in medical contexts...",
        created_by="test_user",
        analysis_data={
            "key_concepts": ["disease", "illness"],
            "usage_patterns": ["medical texts"]
        },
        citations={
            "primary": ["Hippocrates, Aphorisms 1.1"]
        }
    )
    
    assert result["success"] is True
    assert "Analysis of the term" in result["entry"]["analysis_text"]
    assert "key_concepts" in result["entry"]["analysis_data"]
    assert "primary" in result["entry"]["citations"]
    
    # Get lemma with analysis
    lemma = await service.get_lemma_by_text("νόσος")
    assert len(lemma.analyses) > 0
    assert lemma.analyses[0].created_by == "test_user"

@pytest.mark.asyncio
async def test_error_handling(
    db_session: AsyncSession
) -> None:
    """Test error handling in service methods."""
    service = LexicalService(db_session)
    
    # Test invalid lemma
    with pytest.raises(ValueError):
        await service.create_lemma("", language_code="grc")
    
    # Test invalid language code
    with pytest.raises(ValueError):
        await service.create_lemma("test", language_code="invalid")
    
    # Test invalid categories
    with pytest.raises(ValueError):
        await service.create_lemma("test", categories="not_a_list")
    
    # Test invalid translations
    with pytest.raises(ValueError):
        await service.create_lemma("test", translations="not_a_dict")
        
@pytest.mark.asyncio
async def test_batch_create_lemmas(
    db_session: AsyncSession
) -> None:
    """Test batch creation of lemmas."""
    service = LexicalService(db_session)
    
    lemmas_data = [
        {
            "lemma": "φάρμακον",
            "language_code": "grc",
            "categories": ["medical", "drug"],
            "translations": {"en": "drug, medicine"}
        },
        {
            "lemma": "ἰατρός",
            "language_code": "grc",
            "categories": ["medical", "profession"],
            "translations": {"en": "physician, doctor"}
        }
    ]
    
    results = await service.batch_create_lemmas(lemmas_data)
    assert len(results) == 2
    assert all(result["success"] for result in results)
    assert results[0]["entry"]["lemma"] == "φάρμακον"
    assert results[1]["entry"]["lemma"] == "ἰατρός"

@pytest.mark.asyncio
async def test_batch_update_lemmas(
    db_session: AsyncSession,
    sample_lemma: Lemma
) -> None:
    """Test batch updating of lemmas."""
    service = LexicalService(db_session)
    
    # Create additional lemma for batch update
    await service.create_lemma(
        lemma="φάρμακον",
        language_code="grc",
        categories=["medical"]
    )
    
    updates = [
        {
            "lemma": "νόσος",
            "categories": ["medical", "pathology"]
        },
        {
            "lemma": "φάρμακον",
            "categories": ["medical", "pharmacology"]
        }
    ]
    
    results = await service.batch_update_lemmas(updates)
    assert len(results) == 2
    assert all(result["success"] for result in results)
    assert "pathology" in results[0]["entry"]["categories"]
    assert "pharmacology" in results[1]["entry"]["categories"]

@pytest.mark.asyncio
async def test_analysis_management(
    db_session: AsyncSession,
    sample_lemma: Lemma,
    sample_analysis: LemmaAnalysis
) -> None:
    """Test comprehensive analysis management."""
    service = LexicalService(db_session)
    
    # Test updating existing analysis
    result = await service.update_analysis(
        analysis_id=sample_analysis.id,
        analysis_text="Updated analysis...",
        analysis_data={
            "key_concepts": ["updated", "concepts"],
            "significance": "high"
        }
    )
    
    assert result["success"] is True
    assert "Updated analysis" in result["entry"]["analysis_text"]
    assert "significance" in result["entry"]["analysis_data"]
    
    # Test listing analyses for a lemma
    analyses = await service.list_analyses(sample_lemma.lemma)
    assert len(analyses) > 0
    assert analyses[0]["lemma_id"] == sample_lemma.id
    
    # Test deleting analysis
    success = await service.delete_analysis(sample_analysis.id)
    assert success is True
    
    analyses = await service.list_analyses(sample_lemma.lemma)
    assert len(analyses) == 0

@pytest.mark.asyncio
async def test_complex_lemma_queries(
    db_session: AsyncSession
) -> None:
    """Test complex lemma queries and filters."""
    service = LexicalService(db_session)
    
    # Create lemmas with various attributes
    lemmas_data = [
        {
            "lemma": "θεραπεία",
            "language_code": "grc",
            "categories": ["medical", "treatment"],
            "translations": {"en": "treatment"}
        },
        {
            "lemma": "morbus",
            "language_code": "lat",
            "categories": ["medical", "disease"],
            "translations": {"en": "disease"}
        },
        {
            "lemma": "ὑγίεια",
            "language_code": "grc",
            "categories": ["medical", "health"],
            "translations": {"en": "health"}
        }
    ]
    
    for data in lemmas_data:
        await service.create_lemma(**data)
    
    # Test combined language and category filter
    results = await service.list_lemmas(
        language_code="grc",
        category="medical"
    )
    assert len(results) == 2
    assert all(r["language_code"] == "grc" for r in results)
    
    # Test translation search
    results = await service.search_translations("disease")
    assert len(results) == 1
    assert results[0]["lemma"] == "morbus"
    
    # Test category combination
    results = await service.list_lemmas(
        categories=["medical", "treatment"]
    )
    assert len(results) == 1
    assert results[0]["lemma"] == "θεραπεία"

@pytest.mark.asyncio
async def test_analysis_queries(
    db_session: AsyncSession,
    sample_lemma: Lemma
) -> None:
    """Test querying and filtering analyses."""
    service = LexicalService(db_session)
    
    # Create multiple analyses
    analyses_data = [
        {
            "analysis_text": "Primary analysis...",
            "created_by": "user1",
            "analysis_data": {"type": "primary"}
        },
        {
            "analysis_text": "Secondary analysis...",
            "created_by": "user2",
            "analysis_data": {"type": "secondary"}
        }
    ]
    
    for data in analyses_data:
        await service.create_analysis(
            lemma=sample_lemma.lemma,
            **data
        )
    
    # Test filtering by creator
    results = await service.list_analyses(
        sample_lemma.lemma,
        created_by="user1"
    )
    assert len(results) == 1
    assert results[0]["created_by"] == "user1"
    
    # Test filtering by analysis type
    results = await service.list_analyses(
        sample_lemma.lemma,
        analysis_data={"type": "secondary"}
    )
    assert len(results) == 1
    assert results[0]["analysis_data"]["type"] == "secondary"

@pytest.mark.asyncio
async def test_transaction_handling(
    db_session: AsyncSession
) -> None:
    """Test transaction handling in batch operations."""
    service = LexicalService(db_session)
    
    # Test rollback on batch create
    lemmas_data = [
        {
            "lemma": "valid",
            "language_code": "grc"
        },
        {
            "lemma": "",  # Invalid
            "language_code": "grc"
        }
    ]
    
    with pytest.raises(ValueError):
        await service.batch_create_lemmas(lemmas_data)
    
    # Verify no lemmas were created
    results = await service.list_lemmas()
    assert not any(r["lemma"] == "valid" for r in results)
    
    # Test rollback on batch update
    await service.create_lemma(
        lemma="test",
        language_code="grc"
    )
    
    updates = [
        {
            "lemma": "test",
            "categories": ["valid"]
        },
        {
            "lemma": "nonexistent",
            "categories": ["invalid"]
        }
    ]
    
    result = await service.batch_update_lemmas(updates)
    assert not all(r["success"] for r in result)
    
    # Verify original lemma unchanged
    lemma = await service.get_lemma_by_text("test")
    assert not lemma.categories
    
@pytest.mark.asyncio
async def test_concurrent_operations(
    db_session: AsyncSession
) -> None:
    """Test concurrent lemma operations."""
    service = LexicalService(db_session)
    
    # Create base lemma
    await service.create_lemma(
        lemma="test",
        language_code="grc",
        categories=["test"]
    )
    
    # Test concurrent updates
    async def update_categories():
        return await service.update_lemma(
            lemma="test",
            categories=["updated"]
        )
    
    async def update_translations():
        return await service.update_lemma(
            lemma="test",
            translations={"en": "updated"}
        )
    
    results = await asyncio.gather(
        update_categories(),
        update_translations()
    )
    
    assert all(r["success"] for r in results)
    
    # Verify final state
    lemma = await service.get_lemma_by_text("test")
    assert "updated" in lemma.categories
    assert lemma.translations["en"] == "updated"

@pytest.mark.asyncio
async def test_performance_batch_operations(
    db_session: AsyncSession
) -> None:
    """Test performance of batch operations."""
    service = LexicalService(db_session)
    
    # Create large batch of lemmas
    lemmas_data = [
        {
            "lemma": f"test_{i}",
            "language_code": "grc",
            "categories": ["test"],
            "translations": {"en": f"test_{i}"}
        }
        for i in range(100)
    ]
    
    start_time = time.time()
    results = await service.batch_create_lemmas(lemmas_data)
    end_time = time.time()
    
    assert len(results) == 100
    assert all(r["success"] for r in results)
    assert end_time - start_time < 5.0  # Should complete within 5 seconds

@pytest.mark.asyncio
async def test_edge_cases(
    db_session: AsyncSession
) -> None:
    """Test edge cases in lemma operations."""
    service = LexicalService(db_session)
    
    # Test very long lemma
    long_lemma = "α" * 1000
    with pytest.raises(ValueError):
        await service.create_lemma(
            lemma=long_lemma,
            language_code="grc"
        )
    
    # Test special characters in lemma
    special_lemma = "test!@#$%^"
    with pytest.raises(ValueError):
        await service.create_lemma(
            lemma=special_lemma,
            language_code="grc"
        )
    
    # Test empty categories list
    result = await service.create_lemma(
        lemma="test_empty",
        language_code="grc",
        categories=[]
    )
    assert result["success"] is True
    assert result["entry"]["categories"] == []
    
    # Test null values in translations
    result = await service.create_lemma(
        lemma="test_null",
        language_code="grc",
        translations={"en": None}
    )
    assert result["success"] is True
    assert result["entry"]["translations"]["en"] is None

@pytest.mark.asyncio
async def test_search_functionality(
    db_session: AsyncSession
) -> None:
    """Test advanced search functionality."""
    service = LexicalService(db_session)
    
    # Create test data
    test_lemmas = [
        {
            "lemma": "ἄλγος",
            "language_code": "grc",
            "categories": ["medical", "pain"],
            "translations": {"en": "pain, grief"}
        },
        {
            "lemma": "ἄλγημα",
            "language_code": "grc",
            "categories": ["medical", "pain"],
            "translations": {"en": "pain"}
        },
        {
            "lemma": "dolor",
            "language_code": "lat",
            "categories": ["medical", "pain"],
            "translations": {"en": "pain"}
        }
    ]
    
    for data in test_lemmas:
        await service.create_lemma(**data)
    
    # Test fuzzy search
    results = await service.search_lemmas("αλγ")
    assert len(results) == 2
    
    # Test translation search
    results = await service.search_translations("grief")
    assert len(results) == 1
    assert results[0]["lemma"] == "ἄλγος"
    
    # Test category intersection
    results = await service.list_lemmas(
        categories=["medical", "pain"]
    )
    assert len(results) == 3

@pytest.mark.asyncio
async def test_analysis_versioning(
    db_session: AsyncSession,
    sample_lemma: Lemma
) -> None:
    """Test analysis versioning and history."""
    service = LexicalService(db_session)
    
    # Create multiple versions of analysis
    versions = [
        {
            "analysis_text": f"Version {i}",
            "created_by": "test_user",
            "analysis_data": {"version": i}
        }
        for i in range(3)
    ]
    
    for version in versions:
        await service.create_analysis(
            lemma=sample_lemma.lemma,
            **version
        )
    
    # Get analysis history
    history = await service.get_analysis_history(sample_lemma.lemma)
    assert len(history) == 3
    assert [h["analysis_data"]["version"] for h in history] == [2, 1, 0]
    
    # Get specific version
    version = await service.get_analysis_version(
        sample_lemma.lemma,
        version=1
    )
    assert version["analysis_data"]["version"] == 1

@pytest.mark.asyncio
async def test_cleanup(
    db_session: AsyncSession
) -> None:
    """Test cleanup operations."""
    service = LexicalService(db_session)
    
    # Create test data
    await service.create_lemma(
        lemma="test",
        language_code="grc",
        categories=["test"]
    )
    
    # Create orphaned analysis
    analysis = LemmaAnalysis(
        lemma_id=999,  # Non-existent lemma
        analysis_text="Orphaned",
        created_by="test"
    )
    db_session.add(analysis)
    await db_session.commit()
    
    # Run cleanup
    cleaned = await service.cleanup_orphaned_analyses()
    assert cleaned == 1
    
    # Verify cleanup
    analyses = await service.list_analyses("test")
    assert len(analyses) == 0
    
@pytest.mark.asyncio
async def test_validation_rules(
    db_session: AsyncSession
) -> None:
    """Test validation rules for lemma operations."""
    service = LexicalService(db_session)
    
    # Test lemma format validation
    invalid_formats = [
        "123",  # Numbers only
        "test123",  # Mixed with numbers
        "TEST",  # Uppercase
        "τεστ!",  # With punctuation
    ]
    
    for invalid_lemma in invalid_formats:
        with pytest.raises(ValueError, match="Invalid lemma format"):
            await service.create_lemma(
                lemma=invalid_lemma,
                language_code="grc"
            )
    
    # Test language code validation
    valid_codes = ["grc", "lat", "ara"]
    invalid_codes = ["gr", "en", "invalid"]
    
    for code in valid_codes:
        result = await service.create_lemma(
            lemma=f"test_{code}",
            language_code=code
        )
        assert result["success"] is True
    
    for code in invalid_codes:
        with pytest.raises(ValueError, match="Invalid language code"):
            await service.create_lemma(
                lemma="test",
                language_code=code
            )

@pytest.mark.asyncio
async def test_bulk_operations_monitoring(
    db_session: AsyncSession
) -> None:
    """Test monitoring of bulk operations."""
    service = LexicalService(db_session)
    
    # Create test data
    lemmas_data = [
        {
            "lemma": f"test_{i}",
            "language_code": "grc",
            "categories": ["test"]
        }
        for i in range(1000)
    ]
    
    # Test batch size handling
    batch_metrics = []
    
    async def monitor_batch(size: int) -> float:
        start = time.time()
        batch = lemmas_data[:size]
        results = await service.batch_create_lemmas(batch)
        duration = time.time() - start
        batch_metrics.append({
            "size": size,
            "duration": duration,
            "avg_time": duration / size
        })
        return duration
    
    # Test different batch sizes
    batch_sizes = [10, 50, 100, 250]
    for size in batch_sizes:
        await monitor_batch(size)
    
    # Verify performance scales reasonably
    avg_times = [m["avg_time"] for m in batch_metrics]
    assert all(t < 0.1 for t in avg_times)  # Each operation under 100ms
    
    # Verify larger batches are more efficient per item
    assert avg_times[-1] < avg_times[0]  # Last batch more efficient than first

@pytest.mark.asyncio
async def test_data_consistency(
    db_session: AsyncSession
) -> None:
    """Test data consistency across operations."""
    service = LexicalService(db_session)
    
    # Create test lemma with full data
    initial_data = {
        "lemma": "δοκιμή",
        "language_code": "grc",
        "categories": ["test", "example"],
        "translations": {
            "en": "test",
            "de": "Test",
            "fr": "test"
        }
    }
    
    result = await service.create_lemma(**initial_data)
    assert result["success"] is True
    
    # Test partial updates maintain other fields
    update_cases = [
        {"categories": ["updated"]},
        {"translations": {"en": "updated"}},
        {"language_code": "lat"}
    ]
    
    lemma_id = result["entry"]["id"]
    
    for update in update_cases:
        result = await service.update_lemma(
            lemma="δοκιμή",
            **update
        )
        assert result["success"] is True
        
        # Verify other fields maintained
        lemma = await service.get_lemma_by_text("δοκιμή")
        for key, value in initial_data.items():
            if key not in update:
                current_value = getattr(lemma, key)
                assert current_value == value

@pytest.mark.asyncio
async def test_analysis_integrity(
    db_session: AsyncSession,
    sample_lemma: Lemma
) -> None:
    """Test integrity of analysis data."""
    service = LexicalService(db_session)
    
    # Create analysis with complex data
    analysis_data = {
        "lemma": sample_lemma.lemma,
        "analysis_text": "Test analysis",
        "created_by": "test_user",
        "analysis_data": {
            "morphology": {
                "root": "test",
                "suffixes": ["a", "b"]
            },
            "semantics": {
                "domains": ["test"],
                "relations": ["synonym"]
            }
        },
        "citations": {
            "primary": ["test 1.1"],
            "secondary": ["ref 1"]
        }
    }
    
    result = await service.create_analysis(**analysis_data)
    assert result["success"] is True
    
    # Test nested data retrieval
    analysis = await service.get_analysis(result["entry"]["id"])
    assert analysis["analysis_data"]["morphology"]["root"] == "test"
    assert "test 1.1" in analysis["citations"]["primary"]
    
    # Test partial updates maintain nested structure
    update = {
        "analysis_data": {
            "morphology": {
                "root": "updated"
            }
        }
    }
    
    result = await service.update_analysis(
        analysis_id=analysis["id"],
        **update
    )
    
    updated = await service.get_analysis(analysis["id"])
    assert updated["analysis_data"]["morphology"]["root"] == "updated"
    assert updated["analysis_data"]["morphology"]["suffixes"] == ["a", "b"]
    assert updated["analysis_data"]["semantics"] == analysis["analysis_data"]["semantics"]
