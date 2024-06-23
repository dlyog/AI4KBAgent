# app.py

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, make_response
import logging
import os
from state_graph import graph, container
from dotenv import load_dotenv
from websocket_handler import start_websocket_server
import psutil
from utils import generate_response
import signal
from threading import Thread, Event, Lock
import queue
import time
from prompts import SEARCH_PROMPT, FIND_ARTICLE_PROMPT, CONTEXTUAL_PROMPT, GENERIC_ANSWER_PROMPT
from auth import authenticate, login_required, role_required
from notifier import send_teams_notification, send_email_notification, create_service_now_kb
import traceback

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Set a unique, secure secret key

app_config = {
    "teams_webhook_url": os.getenv('TEAMS_WEBHOOK_URL'),
    "email_address": os.getenv('EMAIL_ADDRESS'),
    "servicenow_instance": os.getenv('SERVICENOW_INSTANCE'),
    "servicenow_username": os.getenv('SERVICENOW_USERNAME'),
    "servicenow_password": os.getenv('SERVICENOW_PASSWORD'),
    "mail_server": os.getenv('MAIL_SERVER'),
    "mail_port": int(os.getenv('MAIL_PORT')),
    "mail_default_sender": os.getenv('MAIL_DEFAULT_SENDER'),
    "mail_password": os.getenv('MAIL_PASSWORD'),
    "mail_username": os.getenv('MAIL_USERNAME')
}


# Create a queue with a maximum size of 3
task_queue = queue.Queue(maxsize=3)
queue_lock = Lock()
queue_status = []

def process_queue():
    while True:
        state = task_queue.get()
        if state is None:
            break
        state['status'] = 'in progress'
        run_agent(state)
        state['status'] = 'completed'
        task_queue.task_done()

# Start the worker thread
worker_thread = Thread(target=process_queue)
worker_thread.daemon = True
worker_thread.start()


@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = authenticate(username, password)
        if user:
            session['user'] = user
            if user['role'] == 'Content Developer':
                return "home_content_developer"
            else:
                return "home_regular_user"
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')


# Define the route for explaining text
@app.route('/explain_text', methods=['POST'])
def explain_text():
    data = request.json
    #.debug("Received data: %s", data)

    # Extract blogTitle and selectedText from the request
    blogTitle = data.get('blogTitle')
    selectedText = data.get('selectedText')

    # Log the specific data you're working with
    #logging.debug("Blog Title: %s", blogTitle)
    #logging.debug("Selected Text: %s", selectedText)

    prompt_str = f"""You are an AI trained to provide maximum three lines precise explanations of text content. Your task is to offer an in-depth explanation for the selected text from the blog titled 'Exploring AI Innovations'.

    Provide a clear and comprehensive explanation that makes the concept or information easily understandable. Ensure your explanation is insightful and adds value to the reader's understanding.

    If the selected text does not contain enough context to generate a full explanation, or if it appears too generic or simple, then instead provide a brief overview related to the blog title 'Exploring AI Innovations'. Additionally, inform the user that the selected text may not require  explanation due to its generic or simplistic nature.

    DO NOT add any information not present or implied in the selected text. Aim to clarify, elucidate, and expand upon the given content where possible.

    [SelectedText]
    '{selectedText}'

    [BlogTitle]
    '{blogTitle}'

    In cases where the selected text is too generic or simplistic to necessitate a detailed explanation, offer a concise overview pertinent to the blog title and notify the user accordingly"""                


    ai_response = generate_response(prompt_str, "")

    return jsonify({"explanation": ai_response})


# Define the route for explaining text
@app.route('/summarize_text', methods=['POST'])
def summarize_text():
    data = request.json
    #logging.debug("Received data: %s", data)

    # Extract blogTitle and selectedText from the request
    blogTitle = data.get('blogTitle')
    selectedText = data.get('selectedText')

    # Log the specific data you're working with
    #logging.debug("Blog Title: %s", blogTitle)
    #logging.debug("Selected Text: %s", selectedText)

    prompt_str = f"""You are an AI trained to provide concise summaries within a maximum of three lines. Your task is to distill the essence of the selected text from the blog titled 'Exploring AI Innovations'.

Provide a succinct summary that captures the core ideas or arguments presented. Ensure your summary is precise and conveys the primary information or insight effectively.

If the selected text does not contain enough substance to generate a full summary, or if it appears too broad or simple, then instead offer a brief insight related to the blog title 'Exploring AI Innovations'. Additionally, inform the user that the selected text may not provide substantial content for a detailed summary due to its broad or simplistic nature.

DO NOT introduce any information not present or implied in the selected text. Aim to condense and highlight the main points or insights from the given content where possible.

[SelectedText]
'{selectedText}'

[BlogTitle]
'{blogTitle}'

In cases where the selected text is too broad or simplistic to necessitate a detailed summary, offer a concise insight pertinent to the blog title and notify the user accordingly.<</SYS>>[/INST]"""
            


    ai_response = generate_response(prompt_str, "")

    return jsonify({"summary": ai_response})




@app.route('/home_content_developer')
@login_required
@role_required('Content Developer')
def home_content_developer():
    try:
        articles = list(container.query_items(
            query="SELECT c.id, c.status, c.title, c.servicenow_url FROM c",
            enable_cross_partition_query=True
        ))

        for article in articles:
            if 'servicenow_url' not in article:
                article['servicenow_url'] = 'N/A'

        #logger.info(f"Retrieved articles: {articles}")
        return render_template('home_content_developer.html', articles=articles)
    except Exception as e:
        logger.error(f"Error retrieving articles: {e}")
        return "Error retrieving articles", 500

@app.route('/home_regular_user')
@login_required
@role_required('Regular User')
def home_regular_user():
    try:
        articles = list(container.query_items(
            query="SELECT c.id, c.status, c.title, c.servicenow_url FROM c WHERE c.status = 'Approved' OR c.status = 'Published'",
            enable_cross_partition_query=True
        ))

        for article in articles:
            if 'servicenow_url' not in article:
                article['servicenow_url'] = 'N/A'

        #logger.info(f"Retrieved articles: {articles}")
        return render_template('home_regular_user.html', articles=articles)
    except Exception as e:
        logger.error(f"Error retrieving articles: {e}")
        return "Error retrieving articles", 500



@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    try:
        user = session.get('user')
        if not user:
            return redirect(url_for('login'))
        
        if user['role'] == 'Content Developer':
            return redirect(url_for('home_content_developer'))
        else:
            return redirect(url_for('home_regular_user'))
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return "Error in index route", 500


@app.route('/view/<article_id>', methods=['GET'])
@login_required 
def view_article(article_id):
    try:
        # Retrieve the document first to get the partition key
        query = f"SELECT * FROM c WHERE c.id = '{article_id}'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if not items:
            raise Exception("Document not found")

        article = items[0]

        # Use the partition key from the document to read it
        article = container.read_item(item=article_id, partition_key=article['paper'])
        return render_template('article.html', article=article)
    except Exception as e:
        logger.error(f"Error retrieving article: {e}")
        return "Error retrieving article", 500

@app.route('/edit/<article_id>', methods=['GET'])
@login_required
@role_required('Content Developer')
def edit_article(article_id):
    try:
        query = f"SELECT * FROM c WHERE c.id = '{article_id}'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if not items:
            raise Exception("Document not found")

        article = items[0]
        return render_template('edit_article.html', article=article)
    except Exception as e:
        logger.error(f"Error retrieving article: {e}")
        return "Error retrieving article", 500

@app.route('/update/<article_id>', methods=['POST'])
@login_required
def update_article(article_id):
    try:
        data = request.get_json()
        query = f"SELECT * FROM c WHERE c.id = '{article_id}'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if not items:
            raise Exception("Document not found")

        article = items[0]
        partition_key = article['paper']

        for key, value in data.items():
            article[key] = value

        if article.get('status') == 'Published':
            state = {
                "title": article['title'],
                "summary": article['summary'],
                "category": article['category'],
                "sections": article['sections']
            }

            try:
                # Create the KB article in ServiceNow and update the state with the actual URL
                updated_state = create_service_now_kb(state, app_config)
                article['servicenow_url'] = updated_state["article_url"]

                # Use the updated state for notifications
                logger.error(f"app_config: {app_config}")
                send_teams_notification(updated_state, app_config)
                send_email_notification(updated_state, app_config)
            except Exception as e:
                logger.error(f"Failed to create ServiceNow KB article: {e}")
                traceback.print_exc()
                return jsonify(message="Failed to Publish in ServiceNow. So Update Aborted"), 200

         # Delete the existing item
        container.delete_item(item=article_id, partition_key=partition_key)

        # Create new item with updated data
        container.create_item(body=article)

       

        return "Article updated successfully", 200
    except Exception as e:
        logger.error(f"Error updating article: {e}")
        return jsonify(message="Unepxected Error occured in Updating Article"), 200








@app.route('/delete/<article_id>', methods=['DELETE'])
@login_required
@role_required('Content Developer')
def delete_article(article_id):
    try:
        # Retrieve the document first to get the partition key
        query = f"SELECT * FROM c WHERE c.id = '{article_id}'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if not items:
            raise Exception("Document not found")

        article = items[0]
        partition_key = article['paper']  # Use the correct partition key field
        
        # Log the retrieved article and partition key
        #logger.info(f"Retrieved article for delete: {article}")
        #logger.info(f"Partition key for article: {partition_key}")

        # Delete the document using the correct partition key
        container.delete_item(item=article_id, partition_key=partition_key)
        return "Article deleted successfully", 200
    except Exception as e:
        logger.error(f"Error deleting article: {e}")
        return f"Error deleting article: {e}", 500




@app.route('/search', methods=['GET'])
@login_required 
def search_page():
    return render_template('search.html')

@app.route('/search/results', methods=['POST'])
@login_required
def search_results():
    data = request.json
    query_text = data.get('query')
    chat_history = data.get('history', [])
    
    try:
        # Construct the query to fetch all titles and summaries
        query = (
            f"SELECT c.id, c.title, c.summary FROM c"
        )

        # Execute the query with cross partition enabled
        results = list(container.query_items(query=query, enable_cross_partition_query=True))

        # Log the raw results for debugging
        #logging.info(f"Raw results from Cosmos DB: {results}")

        # Prepare a map of articles based on the query
        articles_map = {article['title']: article['id'] for article in results}
        articles_list = [(article['title'], article['summary']) for article in results]

        # Build the articles string for the prompt
        articles_formatted = "\n".join(
            [f"{index+1}. {title} - {summary}" for index, (title, summary) in enumerate(articles_list)]
        )

        # Format the chat history
        history_formatted = "\n".join([f"{entry['role'].capitalize()}: {entry['message']}" for entry in chat_history])

        # Prepare prompts for OpenAI
        system_prompt = SEARCH_PROMPT.format(
            query_text=query_text,
            articles=articles_formatted,
            history=history_formatted
        )
        user_prompt = query_text

        # Log the final prompt for debugging
        #logging.info(f"System Prompt: {system_prompt}")
        #logging.info(f"User Prompt: {user_prompt}")

        # Send results to OpenAI for reasoning and response generation
        ai_response = generate_response(system_prompt, user_prompt)

        # Extract relevant references from the AI response
        references = ""
        for title, article_id in articles_map.items():
            if title in ai_response:
                base_url = request.host_url.rstrip('/')
                references += f"<a href='{base_url}/view/{article_id}' target='_blank' class='text-blue-500 underline'>{title}</a>\n"

        # Construct the final response
        if references:
            final_response = f"{ai_response}\n\nReferences:\n{references}"
        else:
            final_response = ai_response

        return jsonify({"results": results, "ai_response": final_response})
    except Exception as e:
        logger.error(f"Error performing search: {e}")
        return jsonify({"error": str(e)}), 500

def sanitize_for_formatting(text):
    # Escape curly braces by doubling them
    text = text.replace('{', '{{').replace('}', '}}')
    # Escape backslashes by doubling them
    text = text.replace('\\', '\\\\')
    # Escape double quotes by preceding them with a backslash
    text = text.replace('"', '\\"')
    # Escape single quotes by preceding them with a backslash
    text = text.replace("'", "\\'")
    return text

@app.route('/question', methods=['POST'])
@login_required
def question_results():
    data = request.json
    query_text = data.get('query')

    try:
        # Step 1: Construct the query to fetch all titles and summaries
        query = f"SELECT c.id, c.title, c.summary FROM c"

        # Execute the query with cross partition enabled
        results = list(container.query_items(query=query, enable_cross_partition_query=True))

        # Log the raw results for debugging
        #logging.info(f"Raw results from Cosmos DB: {results}")

        # Prepare the articles string for the LLM
        articles_formatted = "\n".join(
            [f"{index+1}. {article['title']} - {article['summary']}" for index, article in enumerate(results)]
        )

        # Step 2: Identify the most relevant article using an LLM call
        find_article_system_prompt = FIND_ARTICLE_PROMPT.format(
            query_text=sanitize_for_formatting(query_text),
            articles=sanitize_for_formatting(articles_formatted)
        )
        relevant_article_title = generate_response(find_article_system_prompt, query_text)

        # Find the relevant article ID
        relevant_article = next((article for article in results if article['title'] == relevant_article_title), None)

        if relevant_article:
            article_id = relevant_article['id']

            # Step 3: Retrieve the document first to get the partition key
            query = f"SELECT * FROM c WHERE c.id = '{article_id}'"
            items = list(container.query_items(query=query, enable_cross_partition_query=True))

            if not items:
                raise Exception("Document not found")

            article = items[0]

            # Use the partition key from the document to read it
            article = container.read_item(item=article_id, partition_key=article['paper'])

            # Extract the title, section names, and content
            article_title = article['title']
            article_content = "\n".join([f"Section: {section['section_name']}\n{section['content']}" for section in article['sections']])

            # Step 4: Prepare the final prompt for contextual learning
            contextual_system_prompt = CONTEXTUAL_PROMPT.format(
                query_text=query_text,
                article_title=article_title,
                article_content=article_content
            )

            # Log the final prompt for debugging
            #logging.info(f"Contextual System Prompt: {contextual_system_prompt}")

            # Generate the AI response using the final prompt
            ai_response = generate_response(contextual_system_prompt, query_text)

            # Construct the final response with references
            base_url = request.host_url.rstrip('/')
            reference = f"<a href='{base_url}/view/{article_id}' target='_blank' class='text-blue-500 underline'>{article_title}</a>"
            final_response = f"{ai_response}\n\nReferences:\n{reference}"
        else:
            # No relevant article found, generate a generic answer
            generic_system_prompt = GENERIC_ANSWER_PROMPT.format(
                query_text=query_text
            )
            ai_response = generate_response(generic_system_prompt, query_text)
            final_response = f"{ai_response}\n\nNote: This is a generic answer not from a specific document."

        return jsonify({"results": [relevant_article] if relevant_article else [], "ai_response": final_response})
    except Exception as e:
        logging.error(f"Error performing search: {e}")
        return jsonify({"ai_response": str(e)}), 200











@app.route('/generate', methods=['POST'])
@login_required
@role_required('Content Developer')
def generate():
    data = request.json
    topic = data['topic']

    state = {
        'task': topic,
        'title': '',
        'sections': [],
        'current_section_index': 0,
        'revision_number': 0,
        'max_revisions': 1,
        'status': 'queued'
    }

    with queue_lock:
        if task_queue.full():
            return make_response(jsonify({'message': 'Content generation engine is too busy, please try after some time.'}), 503)

        task_queue.put(state)
        queue_status.append(state)

    return jsonify({'message': 'Your request is being processed.'}), 202

@app.route('/queue_status', methods=['GET'])
@login_required
@role_required('Content Developer')
def get_queue_status():
    with queue_lock:
        in_progress_items = [{'topic': item['task'], 'status': item['status']} for item in queue_status if item['status'] == 'in progress']
        return jsonify(in_progress_items), 200

@app.route('/articles', methods=['GET'])
@login_required 
def get_articles():
    articles = list(container.query_items(
        query="SELECT * FROM c",
        enable_cross_partition_query=True
    ))
    return jsonify(articles)

def generate_stylish_html(content):
    html_content = ""
    for section in content:
        html_content += f"<section><h2>{section['section_name']}</h2><p>{section['content']}</p></section>"
    return html_content

def run_agent(initial_state):
    thread = {"configurable": {"thread_id": "1"}, "recursion_limit": 30}
    final_state = None

    for s in graph.stream(initial_state, thread):
        final_state = s

    return final_state

def kill_previous_instance(port):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    os.kill(proc.info['pid'], signal.SIGKILL)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            # Skip processes we don't have permission to access or that no longer exist
            continue

# kill_previous_instance(6789)
import psutil
import socket

def get_pid_using_port(port):
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        for conns in proc.connections(kind='inet'):
            if conns.laddr.port == port:
                return proc.info['pid']  # Return the PID of the first matching process
    return None  # Port not in use

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('0.0.0.0', port)) == 0
    
if __name__ == '__main__':
    
    # port_to_check = 6790
    # if is_port_in_use(port_to_check):
    #     pid = get_pid_using_port(port_to_check)
    #     if pid:
    #         print(f"Port {port_to_check} is in use by process {pid}")
    #     else:
    #         print(f"Port {port_to_check} is in use, but PID couldn't be determined")
    # else:
    #     print(f"Port {port_to_check} is not in use")
    #
    # websocket_thread = Thread(target=start_websocket_server, daemon=True)
    # websocket_thread.start()

    app.run(host='0.0.0.0', port=5011, debug=True)

    #context = ('/etc/ssl/certs/certificate.crt', '/etc/ssl/private/private.key')
    #app.run(host='0.0.0.0', port=5011, debug=True, ssl_context=context)


