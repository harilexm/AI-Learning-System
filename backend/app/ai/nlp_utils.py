import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("WARNING: spaCy model not found. Run: python -m spacy download en_core_web_sm")
    nlp = None

def extract_topics(text):
    """Extract key topics/entities from text using spaCy."""
    if not nlp:
        return []
        
    doc = nlp(text)
    topics = []
    for ent in doc.ents:
        topics.append(ent.text.lower())
    # Also extract noun chunks as topics
    for chunk in doc.noun_chunks:
        if len(chunk.text.split()) <= 3:
            topics.append(chunk.text.lower())
    return list(set(topics))[:10]  # Return top 10 unique topics

def score_difficulty(text):
    """Simple text difficulty scoring using sentence complexity."""
    if not nlp:
        return "beginner"
        
    doc = nlp(text)
    avg_sent_len = sum(len(sent) for sent in doc.sents) / max(len(list(doc.sents)), 1)
    if avg_sent_len > 25: return "advanced"
    if avg_sent_len > 15: return "intermediate"
    return "beginner"
