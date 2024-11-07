import pytest
from sqlmodel import Session, SQLModel, create_engine
from uuid import UUID
from typing import List

from supercog.shared.services import db_connect
# Import your models here
from supercog.engine.db import DocSourceConfig, DocSource, DocIndex
from supercog.engine.all_tools import LocalFolderDocSource

@pytest.fixture(scope="module")
def engine():
    return db_connect("engine")

@pytest.fixture(scope="module")
def session(engine):
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture
def tool_factory_id():
    lfds = LocalFolderDocSource()
    return lfds.id

def test_doc_source_config_relationships(session, tool_factory_id):
    # Create a DocSource
    lfds = LocalFolderDocSource()

    doc_source = DocSource(name="Test Source 1", tool_factory_id=tool_factory_id)
    session.add(doc_source)
    session.commit()

    # Create a DocIndex
    doc_index = DocIndex(name="A big index", tenant_id="t1", user_id="u1")
    session.add(doc_index)
    session.commit()

    # Create a DocSourceConfig
    config = DocSourceConfig(
        doc_source_id=doc_source.id,
        doc_index_id=doc_index.id,
        folder_ids=["folder1", "folder2"],
        file_patterns=["*.txt", "*.pdf"]
    )
    session.add(config)
    session.commit()

    # Test relationships
    assert config.doc_source == doc_source
    assert config.doc_index == doc_index
    assert config in doc_source.configs
    assert config in doc_index.source_configs
    assert isinstance(config.folder_ids, List)
    assert isinstance(config.file_patterns, List)

def test_doc_source_methods(session, tool_factory_id):
    doc_source = DocSource(name="Test Source 1", tool_factory_id=tool_factory_id)
    session.add(doc_source)
    session.commit()

    # Test inherited methods
    assert hasattr(doc_source, '_secret_key')
    assert hasattr(doc_source, 'stuff_secrets')
    assert hasattr(doc_source, 'secret_keys')
    assert hasattr(doc_source, 'delete_secrets')
    assert hasattr(doc_source, 'retrieve_secrets')

def test_doc_index_relationships(session, tool_factory_id):
    doc_source = DocSource(name="Test Source 1", tool_factory_id=tool_factory_id)
    doc_index = DocIndex(name="A big index", tenant_id="t1", user_id="u1")
    session.add(doc_index)
    session.add(doc_source)
    session.commit()

    # Create multiple DocSourceConfigs
    configs = [
        DocSourceConfig(doc_index_id=doc_index.id, doc_source_id=doc_source.id),
        DocSourceConfig(doc_index_id=doc_index.id, doc_source_id=doc_source.id)
    ]
    session.add_all(configs)
    session.commit()

    # Test relationships
    assert len(doc_index.source_configs) == 2
    for config in configs:
        assert config in doc_index.source_configs
        assert isinstance(config.folder_ids, List)
        assert isinstance(config.file_patterns, List)
