# Pipeline Usage Guide

## Overview

The pipeline handles the complete process of loading texts into the database and processing them through the NLP pipeline. It processes texts into divisions - logical units that combine citation and structural components.

## Text Division Structure

### Division Components

1. **Citation Components**:
   ```python
   division = {
       "author_id_field": "0627",      # Author identifier
       "work_number_field": "055",      # Work number
       "epithet_field": None,          # Optional abbreviation
       "fragment_field": None          # Optional fragment reference
   }
   ```

2. **Structural Components**:
   ```python
   division.update({
       "volume": None,                 # Optional volume number
       "chapter": "1",                # Chapter number (defaults to "1")
       "section": None                # Optional section reference
   })
   ```

3. **Lines**:
   - Each division contains an ordered set of lines
   - Lines are normalized to be sequential within each division
   - Line numbers are preserved from the original text when available

### Division Creation Rules

Divisions are created when:
1. A new chapter is encountered in citations
2. Title information is found
3. The TLG citation changes
4. Default chapter "1" is used when no chapter exists

Example Processing:
```
Input:
[TLG0627][055] Hippocrates Work
1.1 First chapter first line
1.2 First chapter second line
2.1 Second chapter first line

Output:
Division 1:
- Chapter: 1
- Lines: [1.1, 1.2]

Division 2:
- Chapter: 2
- Lines: [2.1]
```

## Basic Usage

### Simple Sequential Processing

For small to medium datasets, use the basic sequential processing:

```bash
python -m toolkit.migration.process_full_pipeline \
    --corpus-dir /path/to/texts
```

### Parallel Processing

For larger datasets, enable parallel processing:

```bash
python -m toolkit.migration.process_full_pipeline \
    --corpus-dir /path/to/texts \
    --parallel-loading \
    --max-workers 4
```

## GPU Support

The NLP pipeline automatically detects and uses GPU if available. You can control GPU usage with the following options:

```bash
# Force GPU usage (will fall back to CPU if GPU not available)
python -m toolkit.migration.process_full_pipeline \
    --corpus-dir /path/to/texts \
    --use-gpu

# Force CPU usage even if GPU is available
python -m toolkit.migration.process_full_pipeline \
    --corpus-dir /path/to/texts \
    --no-gpu
```

### GPU Requirements
- CUDA-compatible GPU
- PyTorch with CUDA support installed
- Sufficient GPU memory for batch processing

### GPU Memory Management
- Adjust batch size based on available GPU memory
- For 8GB GPU: recommended batch_size=1000
- For 16GB GPU: can increase to batch_size=2000
- Monitor GPU memory usage during processing

## Command Line Options

### Required Arguments

- `--corpus-dir PATH`
  - Directory containing corpus texts
  - Required
  - Example: `--corpus-dir /data/greek_texts`

### Optional Arguments

#### GPU Options

- `--use-gpu`
  - Enable GPU acceleration for NLP processing
  - Default: Auto-detect GPU availability
  - Example: `--use-gpu`

- `--no-gpu`
  - Force CPU usage even if GPU is available
  - Default: False
  - Example: `--no-gpu`

#### Loading Options

- `--parallel-loading`
  - Enable parallel loading of texts into database
  - Default: False (sequential loading)
  - Example: `--parallel-loading`

- `--loading-batch-size N`
  - Number of texts to load in each batch during parallel loading
  - Default: 5
  - Example: `--loading-batch-size 10`

#### Processing Options

- `--model-path PATH`
  - Custom spaCy model path
  - Default: Uses project's default model
  - Example: `--model-path /models/custom_greek`

- `--batch-size N`
  - Batch size for NLP processing
  - Default: 1000
  - Adjust based on GPU memory if using GPU
  - Example: `--batch-size 2000`

- `--max-workers N`
  - Number of worker processes
  - Default: CPU count
  - Used for both loading (if parallel) and NLP processing
  - Example: `--max-workers 4`

#### Validation Options

- `--no-validate`
  - Skip validation phase
  - Default: False (validation enabled)
  - Example: `--no-validate`

## Common Usage Patterns

### 1. Maximum GPU Performance (Large Datasets)

Use GPU acceleration with optimal batch sizes:

```bash
python -m toolkit.migration.process_full_pipeline \
    --corpus-dir /path/to/texts \
    --use-gpu \
    --parallel-loading \
    --max-workers 4 \
    --batch-size 2000 \
    --loading-batch-size 10
```

### 2. Memory-Constrained Systems

Reduce batch sizes and workers:

```bash
python -m toolkit.migration.process_full_pipeline \
    --corpus-dir /path/to/texts \
    --no-gpu \
    --max-workers 2 \
    --loading-batch-size 3 \
    --batch-size 500
```

### 3. Balanced GPU Processing

Balance GPU and CPU resources:

```bash
python -m toolkit.migration.process_full_pipeline \
    --corpus-dir /path/to/texts \
    --use-gpu \
    --max-workers 4 \
    --batch-size 1000 \
    --loading-batch-size 5
```

## Performance Considerations

### GPU Processing

- GPU acceleration primarily benefits NLP processing
- Loading phase remains CPU/IO bound
- Monitor GPU memory usage with:
  ```bash
  nvidia-smi -l 1  # Updates every second
  ```

### Memory Usage

Formula for estimating GPU memory requirements:
```
GPU_Memory = (batch_size * avg_text_length * model_size) + overhead
```

Recommended settings by GPU memory:
- 8GB GPU: batch_size=1000
- 16GB GPU: batch_size=2000
- 24GB+ GPU: batch_size=3000+

### CPU vs GPU Trade-offs

- GPU best for:
  - Large batch sizes
  - Long texts
  - Complex NLP models
- CPU might be better for:
  - Small texts
  - Small batches
  - Simple processing

## Monitoring

### GPU Monitoring

1. Real-time GPU stats:
```bash
watch -n 1 nvidia-smi
```

2. Process-specific GPU memory:
```bash
nvidia-smi --query-compute-apps=pid,used_memory --format=csv
```

### Pipeline Reports

Reports include GPU-specific information:
- GPU device name
- CUDA version
- Memory usage statistics
- Processing performance metrics

## Troubleshooting

### Common GPU Issues

1. **Out of Memory**
   - Reduce batch size
   - Monitor with nvidia-smi
   - Check for other GPU processes

2. **GPU Not Detected**
   - Verify CUDA installation
   - Check PyTorch CUDA support
   - Update GPU drivers

3. **Performance Issues**
   - Compare GPU vs CPU performance
   - Adjust batch sizes
   - Monitor GPU utilization

## Best Practices

1. **GPU Usage**
   - Start with auto-detection
   - Monitor memory usage
   - Adjust batch sizes based on GPU memory

2. **Batch Sizing**
   - Start with conservative sizes
   - Increase gradually while monitoring
   - Consider text lengths

3. **Resource Balancing**
   - Match worker count to CPU cores
   - Balance GPU and CPU workloads
   - Monitor system resources