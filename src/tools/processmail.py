

from tools.decode import decode_mime_text, extract_novel_content

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
    #print("\nNOVEL BODY:\n", novel_body)
    #print("END NOVEL BODY\n")

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


# Fixed categories for now: make them adaptive later based on actual emails received.
#TODO: Put these in the TAG database !
CATEGORY_KEYWORDS = {
    "Projets": [
        "research", "project", "proposal", "experiment", "data", "analysis",
        "grant", "funding", "call for projects", "WP", "deliverable", "methodology",
        "collaboration", "results", "publication plan", "progress report"
    ],

    "Publications": [
        "manuscript", "submission", "review", "proof", "editor", "journal",
        "conference", "symposium", "call for papers", "acceptance", "revision",
        "citation", "ORCID", "DOI", "presentation", "slides", "abstract"
    ],

    "Encadrement": [
        "PhD", "thesis", "doctoral", "supervision", "student", "internship",
        "report", "meeting", "schedule", "evaluation", "progress", "mentor",
        "master", "defense", "training", "advice", "feedback"
    ],

    "Administration": [
        "university", "faculty", "department", "committee", "evaluation",
        "budget", "HR", "contract", "policy", "regulation", "form",
        "reporting", "audit", "compliance", "teaching", "schedule", "minutes", "mission"
    ],

    "Partenariats": [
        "collaboration", "partner", "consortium", "agreement", "industry",
        "stakeholder", "network", "association", "project partner",
        "memorandum", "MoU", "innovation", "transfer", "outreach",
        "meeting", "funding agency"
    ],
    "Séminaires": ["exposé", "speaker", "title", "abstract","invitation", "will welcome", "accueillerons"],
    "Spam/Promo": ["win", "offer", "lottery", "bonus", "Sir or Madam", "unlisted"],
}

def auto_tag_email(email):
    """Assigns up to 3 tags based on subject and content"""
    matched_tags = set()

    # Check for keywords in subject and body
    for category, keywords in CATEGORY_KEYWORDS.items():
        #TODO:  base on summary as well ? or just summary ?
        if any(word.lower() in email.subject.lower() for word in keywords) or \
           any(word.lower() in email.body.lower() for word in keywords):
            matched_tags.add(category)
            if len(matched_tags) >= 3:  # Limit to 3 tags
                break

    return list(matched_tags)


from database.models import Tag, EmailTag

def update_db_emailtags(email, db):
    # Auto-tagging
    tags = auto_tag_email(email)

    for tag_name in tags:
        # Check if the tag already exists
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
            db.session.commit()  # Commit immediately to ensure tag has an ID

        # Check if the email is already tagged with this tag
        existing_email_tag = EmailTag.query.filter_by(email_id=email.id, tag_id=tag.id).first()
        if not existing_email_tag:
            email_tag = EmailTag(email_id=email.id, tag_id=tag.id)
            db.session.add(email_tag)

    db.session.commit()  # ✅ Save all changes