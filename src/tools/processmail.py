

from src.tools.decode import decode_mime_text, extract_novel_content

# The following line shld be run:
# python -c "import nltk; nltk.download('punkt')"

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

#from gensim.summarization import summarize
import re
from sklearn.feature_extraction.text import TfidfVectorizer


from email_reply_parser import EmailReplyParser

#from transformers import pipeline

def summarize_body(body):

    novel_body = extract_novel_content(body)
    print("\nNOVEL BODY:\n", novel_body)
    print("END NOVEL BODY\n")

    try:
        # Generate the summary with sumy
        parser = PlaintextParser.from_string(novel_body, Tokenizer("english"))
        # Use the LSA summarizer
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, 3)  # Summarize to 2 sentences
        summary_text = "\n\n".join(str(sentence) for sentence in summary)
        # Generate the summary with gensim
        #  summary = summarize(novel_body, ratio=0.3)
        # Generate the summary with transformers
        #summarizer = pipeline("summarization")
        #summary = summarizer(novel_body, max_length=150, min_length=20, do_sample=False)
        print("SUMMARY:", summary_text)
        return  summary_text
    except Exception as e:
        # Handle errors and return failure response
        print(f"Error: {e}")
        return "Team meeting scheduled for tomorrow at 10:00 AM."


def highlight_important_words(text, top_n=5):
    """
    Highlight important words in the text by identifying the top N keywords.

    Args:
        text (str): The input text to analyze and highlight.
        top_n (int): The number of top keywords to highlight.

    Returns:
        str: Text with important words highlighted in HTML.
    """
    # Step 1: Extract keywords using TF-IDF
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([text])
    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.toarray()[0]

    # Get the top N keywords
    important_indices = scores.argsort()[-top_n:][::-1]
    important_words = [feature_names[i] for i in important_indices]

    # Step 2: Highlight keywords in the text
    def replace_with_highlight(match):
        return f"<b>{match.group()}</b>"

    for word in important_words:
        # Use regex to find whole word matches (case-insensitive)
        text = re.sub(rf"\b{re.escape(word)}\b", replace_with_highlight, text, flags=re.IGNORECASE)

    return text



def process_email(email_content):
    # Step 1: Extract the main text (excluding signatures and quoted content)
    parsed_email = EmailReplyParser.parse_reply(email_content)

    # Step 2: Split email into quoted sections and identify authors
    sections = email_content.split("________________________________")
    processed_conversation = []

    # Include the parsed email (newest message) as the first section if it exists
    #if parsed_email.strip():
    #    processed_conversation.append(parsed_email.strip())

    for section in sections:
        # Extract "From" name (if present)
        from_match = re.search(r"De\s*:\s*([\w\s'-]+)", section, re.IGNORECASE)
        author = from_match.group(1).strip() if from_match else None

        # Extract the email body (text without metadata)
        body = re.split(r"(De\s*:|Envoyé\s*:|À\s*:|Cc\s*:|Objet\s*:)", section, flags=re.IGNORECASE)[0]
        body = body.strip()

        # Ignore empty sections
        if body:
            if author:
                processed_conversation.append(f"> {author}:\n\n{body}")
            else:
                processed_conversation.append(body)

    # Step 3: Join processed sections into a conversation format
    return "\n\n".join(processed_conversation)