from typing import AsyncGenerator
import os

from supercog.engine.tool_factory import ToolFactory, ToolCategory
from supercog.engine.doc_source_factory import DocSourceFactory

class WebsiteDocSource(DocSourceFactory):
    def __init__(self):
        super().__init__(
            id = "website_file_source",
            system_name = "Website Documents",
            logo_url=super().logo_from_domain("notion.com"),
            category=ToolCategory.CATEGORY_DOCSRC,
            auth_config = {
            },
            help="""
Load documents from a web site
""",

        )

    def get_documents(self, folder_id: str) -> AsyncGenerator[str, None]:
        """ Yields a list of documents from the indicated folder. """
        pass
