# from datetime import datetime
from langchain_core.prompts import PromptTemplate

# # Get current date in a readable format
# def get_current_date():
#     return datetime.now().strftime("%B %d, %Y")


# query_writer_instructions = """Your goal is to generate sophisticated and diverse web search queries. These queries are intended for an advanced automated web research tool capable of analyzing complex results, following links, and synthesizing information.

# Instructions:
# - Always prefer a single search query, only add another query if the original question requests multiple aspects or elements and one query is not enough.
# - Each query should focus on one specific aspect of the original question.
# - Don't produce more than {number_queries} queries.
# - Queries should be diverse, if the topic is broad, generate more than 1 query.
# - Don't generate multiple similar queries, 1 is enough.
# - Query should ensure that the most current information is gathered. The current date is {current_date}.

# Format: 
# - Format your response as a JSON object with ALL three of these exact keys:
#    - "rationale": Brief explanation of why these queries are relevant
#    - "query": A list of search queries

# Example:

# Topic: What revenue grew more last year apple stock or the number of people buying an iphone
# ```json
# {{
#     "rationale": "To answer this comparative growth question accurately, we need specific data points on Apple's stock performance and iPhone sales metrics. These queries target the precise financial information needed: company revenue trends, product-specific unit sales figures, and stock price movement over the same fiscal period for direct comparison.",
#     "query": ["Apple total revenue growth fiscal year 2024", "iPhone unit sales growth fiscal year 2024", "Apple stock price growth fiscal year 2024"],
# }}
# ```

# Context: {research_topic}"""


# web_searcher_instructions = """Conduct targeted Google Searches to gather the most recent, credible information on "{research_topic}" and synthesize it into a verifiable text artifact.

# Instructions:
# - Query should ensure that the most current information is gathered. The current date is {current_date}.
# - Conduct multiple, diverse searches to gather comprehensive information.
# - Consolidate key findings while meticulously tracking the source(s) for each specific piece of information.
# - The output should be a well-written summary or report based on your search findings. 
# - Only include the information found in the search results, don't make up any information.

# Research Topic:
# {research_topic}
# """

# reflection_instructions = """You are an expert research assistant analyzing summaries about "{research_topic}".

# Instructions:
# - Identify knowledge gaps or areas that need deeper exploration and generate a follow-up query. (1 or multiple).
# - If provided summaries are sufficient to answer the user's question, don't generate a follow-up query.
# - If there is a knowledge gap, generate a follow-up query that would help expand your understanding.
# - Focus on technical details, implementation specifics, or emerging trends that weren't fully covered.

# Requirements:
# - Ensure the follow-up query is self-contained and includes necessary context for web search.

# Output Format:
# - Format your response as a JSON object with these exact keys:
#    - "is_sufficient": true or false
#    - "knowledge_gap": Describe what information is missing or needs clarification
#    - "follow_up_queries": Write a specific question to address this gap

# Example:
# ```json
# {{
#     "is_sufficient": true, // or false
#     "knowledge_gap": "The summary lacks information about performance metrics and benchmarks", // "" if is_sufficient is true
#     "follow_up_queries": ["What are typical performance benchmarks and metrics used to evaluate [specific technology]?"] // [] if is_sufficient is true
# }}
# ```

# Reflect carefully on the Summaries to identify knowledge gaps and produce a follow-up query. Then, produce your output following this JSON format:

# Summaries:
# {summaries}
# """

# answer_instructions = """Generate a high-quality answer to the user's question based on the provided summaries.

# Instructions:
# - The current date is {current_date}.
# - You are the final step of a multi-step research process, don't mention that you are the final step. 
# - You have access to all the information gathered from the previous steps.
# - You have access to the user's question.
# - Generate a high-quality answer to the user's question based on the provided summaries and the user's question.
# - you MUST include all the citations from the summaries in the answer correctly.

# User Context:
# - {research_topic}

# Summaries:
# {summaries}"""



BATCH_ANALYSIS_PROMPT = """
You are an expert product analyst. Your task is to perform sentiment analysis and topic extraction for a batch of customer reviews.
For EACH review in the following JSON list, generate a corresponding JSON object with its sentiment and topics.

Your response MUST be a single JSON object with one key, "analyses", which contains a list of these JSON objects.
The order of the analysis objects in your response list MUST match the order of the reviews in the input list.

Each object in the "analyses" list must have two keys:
1. "sentiment": A string, which must be one of "Positive", "Negative", or "Neutral".
2. "topics": A list of 1 to 3 concise string topics (e.g., ["Battery Life", "Screen Quality"]).

Analyze the following reviews:
---
{review_list_json}
---
"""

NORMALIZE_TOPICS_PROMPT = """
You are a data cleaning expert. I have a list of noisy topic keywords from customer reviews.
Your job is to group similar topics together under a single, standardized canonical name.
RULES:
- Group synonyms (e.g., 'Flavor', 'Taste').
- Correct Pluralization and typos (e.g., 'tasts', 'tastes' -> 'Taste').

Your response MUST be a single JSON object where each key is one of the original noisy topics and its value is the single canonical topic you have assigned it to.

Example Input List: ["Taste", "tastes", "Flavor", "Shipping", "delivery"]
Example JSON Output:
{{
  "Taste": "Taste & Flavor",
  "tastes": "Taste & Flavor",
  "Flavor": "Taste & Flavor",
  "Shipping": "Shipping & Delivery",
  "delivery": "Shipping & Delivery"
}}

Here is the list of topics to normalize:
{unique_topic_list}
"""

TOPIC_SUMMARY_PROMPT = """
Based on the following customer review snippets about the topic '{topic}', write a very concise, 1-3 word summary of the customer sentiment for this topic.
Examples: "sweet and refreshing", "poor quality", "fast shipping"

Snippets:
---
{snippets}
---
"""

EXECUTIVE_SUMMARY_PROMPT = """
You are a senior product analyst writing an executive summary for a product team.
Your summary must be insightful, balanced, and 3-4 sentences long.

INSTRUCTIONS:
1.  Use the high-level **Briefing Document** to understand the most important positive and negative themes.
2.  Use the **Full Time-Ordered Analysis Data** to find specific details and identify any trends over time (e.g., "sentiment has improved recently"). The order of **Full Time-Ordered Analysis Data** is from oldest to newest.
3.  Weave all of these insights together into a fluent final report. Explain *why* customers feel the way they do using the topic summaries.

---
**BRIEFING DOCUMENT:**
- **Product ID:** {product_id}
- **Overall Sentiment:** Positive: {positive_percent}%, Negative: {negative_percent}%, Neutral: {neutral_percent}%
- **Top Positive Topics (with micro-summaries):**
{positive_topic_summaries}
- **Top Negative Topics (with micro-summaries):
{negative_topic_summaries}

**FULL TIME-ORDERED ANALYSIS DATA:**
{analysis_results}
---
"""

# We can also create PromptTemplate objects here for convenience, to be imported by the graph
# sentiment_prompt_template = PromptTemplate.from_template(SENTIMENT_PROMPT)
# topic_prompt_template = PromptTemplate.from_template(TOPIC_PROMPT)
batch_analysis_prompt_template = PromptTemplate.from_template(BATCH_ANALYSIS_PROMPT)
normalize_topics_prompt_template = PromptTemplate.from_template(NORMALIZE_TOPICS_PROMPT)
topic_summary_prompt_template = PromptTemplate.from_template(TOPIC_SUMMARY_PROMPT)
executive_summary_prompt_template = PromptTemplate.from_template(EXECUTIVE_SUMMARY_PROMPT)