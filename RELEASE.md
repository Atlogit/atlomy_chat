# AMTA Release Management

## Release Strategy

### Versioning
- Semantic Versioning (SemVer)
- MAJOR.MINOR.PATCH format
- Pre-release versions use `-alpha`, `-beta`, `-rc` suffixes

### Release Types
1. **Major Release** (MAJOR.0.0)
   - Breaking changes
   - Significant architectural updates
   - Requires migration guide

2. **Minor Release** (0.MINOR.0)
   - New features
   - Backwards-compatible improvements
   - Minimal migration effort

3. **Patch Release** (0.0.PATCH)
   - Bug fixes
   - Security patches
   - Performance improvements

## Release Process

### Preparation
- [ ] Update `CHANGELOG.md`
- [ ] Bump version in `setup.py`
- [ ] Ensure all tests pass
- [ ] Update documentation
- [ ] Create release branch

### Checklist
1. Code Freeze
2. Final Testing
3. Documentation Update
4. Version Bump
5. Git Tag Creation
6. PyPI Publication
7. Docker Image Build

### Release Candidate Workflow
```bash
# Create release branch
git checkout -b release/v1.0.0

# Update version
# Update CHANGELOG.md
# Run final tests
pytest

# Create git tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### Publishing to PyPI
```bash
# Build distribution
python setup.py sdist bdist_wheel

# Upload to PyPI
twine upload dist/*
```

## Post-Release
- Monitor for immediate issues
- Prepare hotfix branch if needed
- Communicate changes to users

## Rollback Procedure
- Revert to previous git tag
- Reinstall previous PyPI version
- Restore database state from backup

## Communication
- Update project website
- Send release notes to mailing list
- Update documentation
