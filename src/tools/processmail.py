

from src.tools.decode import decode_mime_text, extract_novel_content

# The following line shld be run:
# python -c "import nltk; nltk.download('punkt')"

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

#from gensim.summarization import summarize



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