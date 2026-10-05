import re


def analyze_resume(text, keywords):
    clean_text = text or ""
    wanted = {str(k).strip().lower() for k in keywords if str(k).strip()}
    try:
        import nltk
        tokens = nltk.word_tokenize(clean_text)
        tagged = nltk.pos_tag(tokens)
    except (LookupError, ImportError):
        tokens = re.findall(r"[A-Za-z][A-Za-z+#.-]*", clean_text)
        tagged = [(token, "UNKNOWN") for token in tokens]
    lowered = {token.lower() for token in tokens}
    matched = sorted(wanted & lowered)
    return {
        "tokens": tokens,
        "pos_tags": tagged,
        "matched_keywords": matched,
        "skill_match_score": round(len(matched) / max(len(wanted), 1), 4),
        "vector": {word: tokens.count(word) for word in set(tokens)},
    }
