from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def get_recommendations(completed_content_titles, all_available_content):
    """
    Use TF-IDF + cosine similarity to recommend content similar to what student completed.
    """
    if not completed_content_titles or not all_available_content:
        return []

    completed_text = " ".join(completed_content_titles)
    candidate_texts = [c["title"] + " " + (c.get("tags", "") or "") for c in all_available_content]

    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([completed_text] + candidate_texts)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

        ranked = sorted(enumerate(similarities), key=lambda x: x[1], reverse=True)
        return [all_available_content[idx] for idx, score in ranked[:5] if score > 0.1]
    except ValueError:
        # Handles cases where vocab is completely empty
        return []
