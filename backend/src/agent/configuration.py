import os
from pydantic import BaseModel, Field
# from typing import Any, Optional

# from langchain_core.runnables import RunnableConfig

# class Configuration(BaseModel):
#     """The configuration for the agent."""

#     query_generator_model: str = Field(
#         default="gemini-2.0-flash",
#         metadata={
#             "description": "The name of the language model to use for the agent's query generation."
#         },
#     )

#     reflection_model: str = Field(
#         default="gemini-2.5-flash-preview-04-17",
#         metadata={
#             "description": "The name of the language model to use for the agent's reflection."
#         },
#     )

#     answer_model: str = Field(
#         default="gemini-2.5-pro-preview-05-06",
#         metadata={
#             "description": "The name of the language model to use for the agent's answer."
#         },
#     )

#     number_of_initial_queries: int = Field(
#         default=3,
#         metadata={"description": "The number of initial search queries to generate."},
#     )

#     max_research_loops: int = Field(
#         default=2,
#         metadata={"description": "The maximum number of research loops to perform."},
#     )

#     @classmethod
#     def from_runnable_config(
#         cls, config: Optional[RunnableConfig] = None
#     ) -> "Configuration":
#         """Create a Configuration instance from a RunnableConfig."""
#         configurable = (
#             config["configurable"] if config and "configurable" in config else {}
#         )

#         # Get raw values from environment or config
#         raw_values: dict[str, Any] = {
#             name: os.environ.get(name.upper(), configurable.get(name))
#             for name in cls.model_fields.keys()
#         }

#         # Filter out None values
#         values = {k: v for k, v in raw_values.items() if v is not None}

#         return cls(**values)


class AgentConfig(BaseModel):
    """
    A Pydantic model for all project configurations.
    Provides data validation and clear default settings.
    """
    
    # --- GCP Configuration ---
    # This field is required and has no default, it must be provided.
    gcp_project_id: str = Field(
        ..., # The ellipsis (...) marks a field as required.
        description="The Google Cloud Project ID."
    )
    bigquery_dataset: str = Field(
        default="customer_feedback_analyzer_dataset",
        description="The BigQuery dataset containing the review tables."
    )
    bigquery_table: str = Field(
        default="clean_reviews",
        description="The BigQuery table containing the cleaned reviews."
    )
    
    # --- LLM Configuration ---
    gemini_model_name: str = Field(
        default="gemini-2.0-flash",
        description="The specific Gemini model to use for analysis."
    )
    
    # --- Development/Testing Configuration ---
    review_limit_for_testing: int = Field(
        default=50,
        description="A safe limit for the number of reviews to query during testing."
    )
