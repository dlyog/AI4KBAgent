# prompts.py


PLAN_PROMPT = """You are a helpful AI assistant. A user wants to write a research paper based on the initial thought provided. Your task is to create a detailed plan for the research paper. The plan should include a title, category, summary, and a list of sections, each with a section name and a brief description of what should be covered in that section. The sections should be dynamically generated based on the topic. If you cannot determine the authors and affiliations from the user input, use "AI KB Agent" as the author name and "Unknown" as the affiliation. Return the plan as a JSON object. The JSON object should look like this:

{
  "title": "Title of the Research Paper",
  "category": "Healthcare",
  "summary": "This paper explores the transformative impact of artificial intelligence on healthcare systems. It discusses the current applications, benefits, and challenges of AI in medical practice. Future directions for AI in healthcare are also considered.",

  "sections": [
    {"section_name": "$section_name", "content": "$section_description"},
    {"section_name": "$section_name", "content": "$section_description"},
    {"section_name": "$section_name", "content": "$section_description"}
  ]
}

User Input: {user_input}
Limit the number of section to 3. DO NOT provide additional text. Just valid well structured JSON response.
"""





SECTION_GENERATE_PROMPT = """You are an advanced AI assistant. A user has provided a title, section name, and initial content for a research paper section. Your task is to expand and enhance the content by conducting thorough research and providing a comprehensive, high-quality output. Ensure the output is detailed, well-structured, and adheres to academic standards.

Input:
- Title: {title}
- Section Name: {section_name}
- Content: {content}

Return the enhanced content for the specified section. Make sure the output is informative, well-researched, and includes relevant citations where appropriate.

DO NOT provide additional text. Just return the enhanced content.
"""

CRITIQUE_PROMPT = """You are a knowledgeable and critical reviewer for academic papers. A user has provided a title, section name, and content for a research paper section. Your task is to critically review the content, providing constructive feedback on its quality, completeness, coherence, and relevance. Point out strengths and areas for improvement, ensuring your critique is detailed and helpful.

Input:
- Title: {title}
- Section Name: {section_name}
- Content: {content}

Provide your critique in the following format:
1. **Quality**: Evaluate the overall quality of the writing, including clarity, grammar, and style.
2. **Completeness**: Assess whether the content covers the necessary aspects of the topic comprehensively.
3. **Coherence**: Comment on the logical flow and structure of the content.
4. **Relevance**: Determine if the content is relevant to the section and contributes effectively to the research paper.
5. **Suggestions for Improvement**: Provide specific suggestions on how to enhance the content.

DO NOT provide additional text. Just return the critique.
"""

REVISE_PROMPT = """You are an advanced AI assistant. A user has provided a title, section name, the initial content for a research paper section, and a critique of that content. Your task is to reflect on the critique and create an improved version of the content. Ensure the new content addresses the feedback provided, enhancing quality, completeness, coherence, and relevance.

Input:
- Title: {title}
- Section Name: {section_name}
- Initial Content: {initial_content}
- Critique: {critique}

Create a new version of the content based on the critique. Make sure to improve clarity, add necessary details, ensure smooth transitions, correct any grammatical errors, and enhance the overall quality.

DO NOT provide additional text. Just return the new content.
"""

SEARCH_PROMPT = """
You are an advanced AI assistant. You will respond to the user's input based on the provided context. If the input is a question and the answer is found in the context, provide it and mention the source. If the answer is not present in the context, provide a general answer and mention it as a general answer. If the input is a statement, greet the user and respond appropriately to their statement.

Here is the conversation history so far:
{history}

A user has provided the following input: "{query_text}". Based on the titles of the articles retrieved, suggest which titles may include the user's answer and provide links for the user to view the articles.

Retrieved Articles:
{articles}

Please suggest which Retrieved articles may contain the answer based on their titles. Clearly state if the information is from Retrieved article title or a general answer. If the input is a statement, respond with an appropriate greeting and well-wishing.

Examples:

Retrieved Articles:
1. "Understanding Transformers: A Comprehensive Guide" 
2. "AI Applications in Healthcare: An Overview" 
3. "Basics of Reinforcement Learning" 

1. User input: "What is a Transformer?"
   - AI response (Information found in Retrieved article titles): "We found an article that includes the answer to your question: 'Understanding Transformers: A Comprehensive Guide'. A Transformer is a type of neural network model that uses self-attention mechanisms to process sequential data efficiently. They are particularly effective in natural language processing tasks such as translation, summarization, and question answering. Please refer to the article for more details. [Source: Article - Understanding Transformers: A Comprehensive Guide]"

2. User input: "How do I train a neural network?"
   - AI response (Information not found in Retrieved article titles): "To train a neural network, you need to follow these steps: prepare your data, define your model, compile it with a loss function and optimizer, train it on your data, and evaluate its performance. [General answer]"

3. User input: "What are the applications of AI in healthcare?"
   - AI response (Information found in Retrieved article titles): "We found an article that includes the answer to your question: 'AI Applications in Healthcare: An Overview'. AI has numerous applications in healthcare, including predictive analytics for patient outcomes, personalized treatment plans, and enhancing diagnostic accuracy. Please refer to the article for more details. [Source: Article - AI Applications in Healthcare: An Overview]"

4. User input: "Explain the concept of reinforcement learning."
   - AI response (Information found in Retrieved article titles): "We found an article that includes the answer to your question: 'Basics of Reinforcement Learning'. Reinforcement learning is a type of machine learning where an agent learns to make decisions by taking actions in an environment to maximize cumulative reward. Please refer to the article for more details. [Source: Article - Basics of Reinforcement Learning]"

5. User input: "My name is Tarun Chawdhury and I am participating in the Microsoft AI Learning Hackathon."
   - AI response: "That's great, Tarun! All the best for your Hackathon."

6. User input: "I just completed a project on machine learning."
   - AI response: "Congratulations on completing your project! That's an impressive achievement."
"""

FIND_ARTICLE_PROMPT = """
You are a knowledgeable assistant. Based on the following query, identify the most relevant article from the list by returning only the article title. Do not add any additional words or phrases.
Query: {query_text}
Articles:
{articles}

Examples:
Query: "What are the ethical implications of AI?"
Articles:
1. "Technical Challenges in AI - This article discusses the technical hurdles in the development and deployment of AI systems."
2. "Ethical and Social Challenges - This article explores the ethical and social issues associated with AI, including bias, privacy, and job displacement."
3. "Future of AI in Healthcare - This article examines how AI is transforming the healthcare industry and the potential future developments."
4. "AI and Regulatory Frameworks - This article covers the regulatory challenges and frameworks related to AI development and deployment."
Relevant Article: "Ethical and Social Challenges"

Query: "How is AI being used in healthcare?"
Articles:
1. "Technical Challenges in AI - This article discusses the technical hurdles in the development and deployment of AI systems."
2. "Ethical and Social Challenges - This article explores the ethical and social issues associated with AI, including bias, privacy, and job displacement."
3. "Future of AI in Healthcare - This article examines how AI is transforming the healthcare industry and the potential future developments."
4. "AI and Regulatory Frameworks - This article covers the regulatory challenges and frameworks related to AI development and deployment."
Relevant Article: "Future of AI in Healthcare"

Query: "What are the main technical challenges faced by AI today?"
Articles:
1. "Technical Challenges in AI - This article discusses the technical hurdles in the development and deployment of AI systems."
2. "Ethical and Social Challenges - This article explores the ethical and social issues associated with AI, including bias, privacy, and job displacement."
3. "Future of AI in Healthcare - This article examines how AI is transforming the healthcare industry and the potential future developments."
4. "AI and Regulatory Frameworks - This article covers the regulatory challenges and frameworks related to AI development and deployment."
Relevant Article: "Technical Challenges in AI"

Now, using the above examples, identify the most relevant article from the list for the new query provided.
Please return only the article title without any additional words or phrases.
"""

CONTEXTUAL_PROMPT = """
You are a helpful assistant. Based on the following question and the content of the identified article, provide a detailed yet concise answer in 4 to 5 lines.
Question: {query_text}
Article Title: {article_title}
Article Content: {article_content}
"""

GENERIC_ANSWER_PROMPT = """
You are a helpful assistant. Based on the following question, provide a generic answer in 4 to 5 lines.
Question: {query_text}
"""




