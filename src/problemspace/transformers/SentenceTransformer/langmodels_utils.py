import re
from typing import List, Tuple
from problemspace.exceptions.TransformerException import TransformerException


def get_text(prompt: str,
             force_words: List[str],
             model,
             tokenizer,
             group_size: int = 10,
             max_groups: int = 10,
             num_return_sequences: int = 1) -> Tuple[List[str], List[int]]:
    """
    Generates text by trying to include multiple words.
    """
    inputs = tokenizer(prompt, return_tensors="pt")
    input_ids = inputs.input_ids

    assert len(force_words) >= 1, "Lang-Model Transformer. Input list of words has no words"
    force_words = force_words[:min(len(force_words), group_size * max_groups)]
    if len(force_words) < group_size:
        group_size = len(force_words)
    no_splits = len(force_words) // group_size
    max_new_tokens = 20 * no_splits

    force_words_ids_flexible = []
    for split in range(no_splits):
        start = split * group_size
        end = start + group_size
        force_words_ids_flexible += [
            tokenizer(force_words[start:end], add_prefix_space=True, add_special_tokens=False).input_ids,
        ]

    inputs.input_ids = inputs.input_ids

    generate_ids = model.generate(input_ids,
                                  early_stopping=True,
                                  eos_token_id=tokenizer('.').input_ids.pop(),
                                  max_new_tokens=max_new_tokens,
                                  num_beams=10,
                                  num_return_sequences=num_return_sequences,
                                  no_repeat_ngram_size=1,
                                  force_words_ids=force_words_ids_flexible)
    outs = tokenizer.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)

    scores = []
    for out in outs:
        words = re.findall(r'(\w+)', out.lower())

        scores.append(len(set.intersection(set(words), set(force_words))))

    return outs, scores


def clean_general_paper_text(text: str) -> str:
    """ Clean text"""

    # 1. Unify whitespaces and so on, e.g. avoid "  " -> " "
    data = ' '.join(text.split())  # splitlines

    # 2. Replace non-ascii symbols
    # data = ''.join([i if ord(i) < 128 else ' ' for i in data])

    # 3. Misc.
    replace_regex = [
        (r"https?://\S+", "<url>"),  # URLs
        (r"\[\d+\]", ""),  # Citations
        (r"\s\[.*]", ""),
        (r"\[.*]", ""),
        (r"<.*?>", "") # <...>
    ]
    for x, y in replace_regex:
        data = re.sub(x, y, data)

    return data


def process_created_text(created_text: str, nlp) -> str:
    """
    Processing text further.
    """
    # 1. Split text into sentences
    doc = nlp(created_text)
    sentences = [sent for sent in doc.sents]
    if len(sentences) == 0:
        raise TransformerException("ProblemSpace: No sentence created in OurFinedTunedLangModelTransformer")

    # 2. Check sentence end
    # Here, we check if last character is a point "." to close the sentence. If not, we add it.
    if not sentences[-1][-1].is_punct:
        sentences = [str(s).strip() for s in sentences]
        sentences[-1] += "."
    else:
        sentences = [str(s).strip() for s in sentences]

    # 3. Create text again
    new_text = " ".join(sentences)
    new_text = new_text.replace("_", "\_")
    new_text = new_text.replace("&", "\&")

    return new_text
