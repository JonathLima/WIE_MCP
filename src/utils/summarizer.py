from src.utils.text import split_into_sentences as _split_into_sentences

def extractive_summary(
    text: str,
    num_sentences: int = 3,
    max_length: int = 1000,
) -> str:
    if not text or not text.strip():
        return ""

    sentences = _split_into_sentences(text)
    if not sentences:
        return ""

    if len(sentences) <= num_sentences:
        return " ".join(sentences[:num_sentences])

    sentence_scores: list[tuple[float, str]] = []
    for i, sentence in enumerate(sentences):
        score = 0.0
        words = len(sentence.split())
        if 5 <= words <= 40:
            score += 1.0
        if sentence[0].isupper():
            score += 0.3
        if i < 3:
            score += 0.5
        if any(kw in sentence.lower() for kw in ["introduction", "overview", "summary", "conclusion"]):
            score += 0.3
        sentence_scores.append((score, sentence))

    sentence_scores.sort(key=lambda x: -x[0])
    top_sentences = [s for _, s in sentence_scores[:num_sentences]]

    original_order = [(i, s) for i, s in enumerate(sentences)]
    top_in_order = sorted(
        [(i, s) for i, s in original_order if s in top_sentences],
        key=lambda x: x[0]
    )
    summary = " ".join(s for _, s in top_in_order)

    if len(summary) > max_length:
        summary = summary[:max_length]
        last_period = summary.rfind(".")
        if last_period > max_length * 0.7:
            summary = summary[:last_period + 1]

    return summary