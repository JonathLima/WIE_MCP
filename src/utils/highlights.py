from src.utils.text import split_into_sentences as _split_into_sentences

def _score_sentence(sentence: str, query_terms: list[str]) -> float:
    sentence_lower = sentence.lower()
    score = 0.0
    for term in query_terms:
        term_lower = term.lower()
        if term_lower in sentence_lower:
            score += 1.0
            if sentence_lower.startswith(term_lower):
                score += 0.5
    return score

def extract_highlights(
    text: str,
    query: str,
    num_sentences: int = 3,
    max_sentence_length: int = 500,
) -> list[str]:
    if not text or not query:
        return []

    sentences = _split_into_sentences(text)
    if not sentences:
        return []

    query_terms = query.split()
    scored = []
    for sentence in sentences:
        if len(sentence) > max_sentence_length:
            continue
        score = _score_sentence(sentence, query_terms)
        if score > 0:
            scored.append((score, sentence))

    scored.sort(key=lambda x: -x[0])
    highlights = [sentence for _, sentence in scored[:num_sentences]]

    if len(highlights) < num_sentences:
        unscored = [s for s in sentences if s not in highlights]
        for s in unscored:
            if len(highlights) >= num_sentences:
                break
            highlights.append(s)

    return highlights[:num_sentences]
