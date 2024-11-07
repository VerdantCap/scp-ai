# Retrival Augmented Generation

Supercog suppports RAG so that people can add knowledge for use by their agents.

The basic use of RAG is answering questions based on some searchable corpus of knowledge.
We may come up with other cool uses of RAG however in more agentic use cases.

## Basic model

We support RAG via these models:

`DocSourceFactory(ToolFactory)`

This is the base class for "tools" that can fetch documents from some doc source.
A doc source typically needs the id of or more folders from which to pull documents.
You can query the DocSource for the list of candidate folders.

Generally the folder list for the DocSource is kept as part of the _attachment_ of
the DocSource to a DocIndex. This allows us to create separate indexes from different
folders using the same DocSource credentials.

`DocSource`

This is the database model that represents a stored authenticated connection to some
DocSource.

`DocIndex`

The DocIndex is a searchable index of docs. It can hold docs given to it directly, or it can
index docs that it pulls from one or more configured DocIndexes.

The DocIndex lets us add and remove docs, and it reports it status in terms of indexing
progress, number of docs and chunks, etc.. A DocIndex also should specify its embedding
model, summarization rules, metadata properties, etc...

`DocSourceConfig` is a join model that configures a DocSource as input to a DocIndex.


### standard metadata

Every DocIndex should include at least the following metadata for each doc:

    - name
    - url
    - time_added (time doc was added to the index)
    - doc_timestamp (timestamp from the doc itself)
    - author (some identifier of the doc author)
    - mime_type (document mime type)
    - size (length of the doc in bytes)
    - characters (count of text characters extracted from the doc)

`Retriever`

A retriever is a class that performs a query against one or more DocIndexes and retrieves
content to add to the LLM context.

## RAGService

The `RAGService` is an API service that manages DocIndexes. You can upload docs via
API into an index, or attach a DocSource to the index. The RAGService is responsible
for managing the contents of many DocIndexes.

These are the basic operations:
(You can assume that the DocIndex object is already created.)

- add_file_to_index(index_id, file)
- start_indexing_job(doc_index_id, doc_source_config_id)
  <- returns a "job_id" for the indexing job created to index this source
- get_indexing_job_status(job_id)
    -> returns status of the indexing job
- tail_indexing_job(job_id)
    -> returns synchronous log of indexing job, so we can show indexing in "real time" the user
- detach_docsource_from_index(index_id, doc_source_id)
- list_docsources(index_id)
- get_index_info(index_id)
    -> returns number of docs, latest doc added, number of chunks

- query_index(index_id, query: str, query_type: str, properites: dict)
    -> queries the index for docs matching "query"
    - query_type can indicate "vector" or "hybrid"
    - if properties are provided they have to match the metadata in the records
  <-- returns a set of doc matches:
        doc_id, time_added, doc_timestamp, chunk, locator, score, metadata


The RAGService should have its on FastAPI endpoints. We will call it via API call
from the Agentsvc.

## Retrieval

Any Agent can have a list of DocIndexes that are attached to it:

    agent.doc_indexes: list[doc_index_id]
    agent.rag_strategy: function | always | confidence | smart

Agents can have a few different strategies for when they access their Rag indexes.

**function**    - We will attach "index_search" functions to the agent which it can
decide to use or not on each turn.

**always**      - We will create a Retriever which always queries for documents from the indexes
on every prompt and injects the resulting info into the LLM context.

**confidence**    - Same version as _always_ but with a high matching threshold so only
longer prompts and higher score chunks are returned.

**smart**       - We run some "classifier" on the prompt to decide if this is a "knowledge question"
and thus whether to call the retriever or not.

This logic will be implemented inside the `Agentsvc` (in ChatEngine.py).

## The indexes available to an agent

Each agent will have access to their _users's_ set of RAG indexes. An index could be
owned by the user or shared in their tenant.

Each index has a _name_ which the user should use to describe the type of knowledge 
contained in the index. But an index could be "single corpus" or "multi-corpus" depending
on what the user wants to achieve.

Each user will get a default index, _Personal Knowledge_ to which documents can be added
by default. So any file uploaded in a chat to Supercog will be added to this index.


