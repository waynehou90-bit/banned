# Project setup checklist

## 1. Run the GitHub workflow

Open the repository Actions tab and run:

```text
Build ChatGPT Project Source Packs
```

Recommended inputs:

```text
packs: leave empty
include_txt: false
commit_results: true
```

After the workflow completes, the repository should contain generated folders under:

```text
project_sources/
```

Each folder should include:

```text
README.md
chunks.md
chunks.jsonl
manifest.json
```

## 2. Local fallback

If the workflow fails, run locally:

```bash
git clone https://github.com/waynehou90-bit/banned.git
cd banned
git checkout json
bash scripts/build_project_packs.sh

git add project_sources
git commit -m "Add default Project source packs"
git push origin json
```

Export selected packs only:

```bash
PACKS="suyu-taoyong maozedong-pishi" bash scripts/build_project_packs.sh
```

## 3. Connect the repository to ChatGPT Project

In the target Project, add a GitHub source and select:

```text
waynehou90-bit/banned
```

Wait for repository indexing to finish.

## 4. Add Project instructions

Copy the instruction block from:

```text
docs/HISTORY_PROJECT_INSTRUCTIONS.md
```

Paste it into the target Project instructions.

## 5. Test query

Use a test prompt like:

```text
Please search the project_sources packs in waynehou90-bit/banned first. Answer using citation_id, title, date, source, file_path, and chunk_index.
```

## 6. Success criteria

The Project should be able to find files like:

```text
project_sources/suyu-taoyong/chunks.md
project_sources/maozedong-pishi/chunks.md
```

A grounded answer should include:

```text
citation_id
title
date
source
file_path
chunk_index
```

## Boundary

The Project can directly search generated files committed under `project_sources/`.
It cannot directly execute the local SQLite database, read local `data/raw/`, or call a local API endpoint.
