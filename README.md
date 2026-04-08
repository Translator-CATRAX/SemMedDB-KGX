# SemMedDB-KGX: Uncapped SemMedDB for PMID Checker

Uncapped version of the SemMedDB ingest from the [NCATS Translator Ingests Pipeline](https://github.com/NCATSTranslator/translator-ingests) (DogPark), produced for the Penn State PMID Checker project.

The decision to use the post-transform, normalized version of SemMedDB for PMID Checker was made during a Zoom meeting with David Koslicki, Chunyu Ma, Matt Brush, Evan Morris, Sierra Moxon, and Adilbek Bazarkulov.

## Files to Use for PMID Checker

After cloning this repo and running the download script, the data files live directly inside the repo:

```
SemMedDB-KGX/
  README.md
  download_semmeddb_uncapped.py
  data/
    normalized_edges.jsonl          <-- use this (11 GB, 1,725,595 edges with all PMIDs)
    normalized_nodes.jsonl          <-- use this (35 MB, 69,577 nodes)
    node_normalization_map.json     <-- CURIE traceability map
    semmeddb_uncapped_edges.jsonl   <-- pre-normalization edges (transform stage)
    semmeddb_uncapped_nodes.jsonl   <-- pre-normalization nodes (transform stage)
    merged_edges.jsonl              <-- deduplicated edges (post-merge)
    merged_nodes.jsonl              <-- deduplicated nodes (post-merge)
    predicate_map.json
    normalization-metadata.json
    merge_metadata.json
    transform-metadata.json
    graph-metadata.json
    ingest-metadata.json
    validation-report.json
```

Use `normalized_edges.jsonl` and `normalized_nodes.jsonl`. These have canonical CURIEs (matching the production Translator KG) and each edge maps 1:1 to a transform-stage edge, so traceability is preserved. The `node_normalization_map.json` maps each canonical CURIE back to the original identifier if needed.

## Quick Start

```bash
git clone https://github.com/Translator-CATRAX/SemMedDB-KGX.git
cd SemMedDB-KGX
python download_semmeddb_uncapped.py
```

This downloads the zipped data from S3 and extracts it into `data/` inside the repo.

## Data Examples

### Example: Normalized Node

Each line in `normalized_nodes.jsonl` is a JSON object representing one node. The Node Normalizer adds `name`, `equivalent_identifiers`, `information_content`, and `description`.

```json
{
  "id": "NCBIGene:100",
  "category": ["biolink:Gene", "biolink:GeneOrGeneProduct", "biolink:Protein", ...],
  "name": "ADA",
  "equivalent_identifiers": [
    "NCBIGene:100",
    "ENSEMBL:ENSG00000196839",
    "HGNC:186",
    "OMIM:608958",
    "UniProtKB:P00813",
    "PR:P00813",
    ...
  ],
  "information_content": 88.2,
  "description": "adenosine deaminase"
}
```

### Example: Normalized Edge (typical, 4 PMIDs)

Each line in `normalized_edges.jsonl` is a JSON object representing one edge. The `publications` field contains all PMIDs, and `has_supporting_studies` contains the extracted sentences from each paper.

```json
{
  "id": "urn:uuid:662b9b5c-3a92-41bd-95b1-b4030bb9cf9a",
  "category": ["biolink:Association"],
  "subject": "NCBIGene:100",
  "predicate": "biolink:affects",
  "object": "UMLS:C0040649",
  "publications": [
    "PMID:2843522",
    "PMID:3047400",
    "PMID:3529081",
    "PMID:7961409"
  ],
  "sources": [
    {
      "resource_id": "infores:semmeddb",
      "resource_role": "primary_knowledge_source"
    }
  ],
  "knowledge_level": "not_provided",
  "agent_type": "text_mining_agent",
  "has_supporting_studies": {
    "urn:uuid:43aac09a-...": {
      "category": ["biolink:Study"],
      "has_study_results": [
        {
          "category": ["biolink:TextMiningStudyResult"],
          "xref": ["PMID:2843522"],
          "supporting_text": [
            "Here we present evidence that Ada protein is activated as a transcriptional regulator through a direct methylation by certain methylating agents."
          ]
        },
        {
          "xref": ["PMID:3047400"],
          "supporting_text": [
            "These results are compatible with the idea that methylation of the cysteine residue at position 69 renders Ada protein active as a transcriptional regulator..."
          ]
        }
      ]
    }
  }
}
```

### Example: Uncapped Edge (7,003 PMIDs)

This is why the uncapped version exists. The production pipeline would cap this edge to ~200 PMIDs. Here all 7,003 are retained.

```json
{
  "id": "urn:uuid:85185d06-d825-4fca-9a84-2cd02283d5d5",
  "category": ["biolink:Association"],
  "subject": "UMLS:C0041618",
  "predicate": "biolink:located_in",
  "object": "UBERON:0000916",
  "publications": [
    "PMID:10021689",
    "PMID:10022141",
    "PMID:10022142",
    "PMID:10022644",
    "PMID:10023401",
    "... (7,003 PMIDs total)"
  ],
  "sources": [
    {
      "resource_id": "infores:semmeddb",
      "resource_role": "primary_knowledge_source"
    }
  ],
  "knowledge_level": "not_provided",
  "agent_type": "text_mining_agent"
}
```

## Background

The Translator Ingests Pipeline transforms biomedical databases into Biolink Model knowledge graphs. SemMedDB is one of these sources -- literature-derived semantic predications extracted by SemRep from PubMed, pre-processed through RTX-KG2.

The production pipeline applies a publication cap (max ~200 PMIDs per edge) because some SemMedDB edges have 60,000+ PMIDs. For the PMID Checker, the full set of PMIDs is needed so the LLM can evaluate all (edge, PMID) pairs. This version retains all PMIDs per edge.

## Data Source

- Source file: `kg2.10.3-semmeddb-edges.jsonl.gz` from [RTX-KG2 public S3](https://rtx-kg2-public.s3.us-west-2.amazonaws.com/kg2.10.3-semmeddb-edges.jsonl.gz)
- Source version: `semmeddb-2023-kg2.10.3` (static -- SemMedDB source data does not change)

## Pipeline Stages and Output Files

The pipeline processes SemMedDB through sequential stages. Each stage produces its own output files.

### Stage 1: Transform

The transform stage applies filtering and converts raw KG2 edges into Biolink Model entities.

Filters applied (recommended by Colleen Xu and Andrew Su):
- Domain/range exclusion -- removes edges where `domain_range_exclusion == true`
- Publication count -- requires more than 3 publications per edge
- BTE-excluded predicates -- skips edges with predicates that BTE removes (`compared_with`, `isa`, `measures`, `higher_than`, `lower_than`)
- No publication cap -- this version retains all PMIDs per edge

Output files (in `transform_892b6acb/`):

| File | Size | Description |
|------|------|-------------|
| `semmeddb_uncapped_nodes.jsonl` | 4 MB | Biolink nodes (genes, chemicals, diseases, etc.) extracted from edges |
| `semmeddb_uncapped_edges.jsonl` | 11 GB | Biolink associations with all publications, qualifiers, and supporting study text |

Transform stats:
- Total edges processed: 21,355,695
- Edges emitted (>3 PMIDs each): 1,725,595
- Unique nodes extracted: 69,577
- Domain/range exclusion skipped: 3,585,908
- Low publication count skipped: 15,912,614
- BTE-excluded predicate skipped: 131,578

CURIEs at this stage are the original identifiers from KG2 (e.g. `UMLS:C0011849`, `NCBIGene:3643`, `CHEBI:6801`).

### Stage 2: Node Normalization

The normalization stage calls the [Translator Node Normalizer API](https://nodenormalization-sri.renci.org/) to map CURIEs to canonical identifiers used across the Translator ecosystem.

What changes:
- CURIEs are remapped to canonical forms (e.g. `UMLS:C0011849` -> `MONDO:0005148`)
- Nodes gain `name`, `description`, `equivalent_identifiers`, and `information_content` from the normalizer
- Predicates are normalized to canonical Biolink predicates

Output files (in `transform_892b6acb/normalization_2025sep1/`):

| File | Size | Description |
|------|------|-------------|
| `normalized_nodes.jsonl` | 35 MB | Nodes with canonical CURIEs, names, and equivalent identifiers |
| `normalized_edges.jsonl` | 11 GB | Edges with canonical CURIEs and normalized predicates. 1:1 mapping to transform-stage edges. |
| `merged_nodes.jsonl` | 34 MB | Deduplicated nodes after single-source merge |
| `merged_edges.jsonl` | 9.7 GB | Deduplicated edges after single-source merge. Edges with the same subject-predicate-object triple get combined, so one merged edge can represent multiple pre-normalization edges. |
| `node_normalization_map.json` | -- | Mapping from original CURIE to canonical CURIE (useful for traceability) |
| `predicate_map.json` | -- | Mapping of predicate normalizations applied |

## Reproducibility

### Source Code

- Pipeline repository: [NCATSTranslator/translator-ingests](https://github.com/NCATSTranslator/translator-ingests)
- Branch: [`semmeddb_uncapped`](https://github.com/NCATSTranslator/translator-ingests/tree/semmeddb_uncapped)
- Commit: `3e99af002dfe8292387ddf542729694194c1ecb0`
- Ingest directory: `src/translator_ingest/ingests/semmeddb_uncapped/`
- Transform hash: `892b6acb`

### Dependency Versions

| Package | Version | Notes |
|---------|---------|-------|
| Python | >= 3.12, < 3.14 | |
| biolink-model | 4.3.6.post107.dev0+77fc44bdc | Pinned to `master` at commit `77fc44bdc` |
| bmt | 1.4.6.post17.dev0+2796a0b | Pinned to `master` at commit `2796a0b` |
| koza | 2.1.1 | Transform framework |
| robokop-orion | 0.1.14 | Normalization and merging |
| linkml | 1.9.4 | Schema validation |
| linkml-runtime | 1.9.5 | |
| pydantic | 2.12.5 | |
| Node Normalizer | 2025sep1 | External API version at time of run |

### How to Reproduce from Source

If you want to re-run the pipeline instead of downloading the pre-built output:

```bash
git clone https://github.com/NCATSTranslator/translator-ingests.git
cd translator-ingests
git checkout semmeddb_uncapped
uv sync
make run SOURCES="semmeddb_uncapped"
```

Output will be in `data/semmeddb_uncapped/semmeddb-2023-kg2.10.3/transform_892b6acb/`.

### Timestamp

- Generated: 2026-04-07
- SemMedDB source data: static (kg2.10.3, 2023 extraction)
- Node Normalizer version: `2025sep1` (may differ if reproduced later)
