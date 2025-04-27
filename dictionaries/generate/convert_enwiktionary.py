import sys
import re
import html
import itertools
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger(__name__)

# This script processes Wiktionary data to extract and clean word pairs in two languages,
# generates phrase combinations, and writes them to an output file (dictionary).


def wiki_to_text(wiki_text):
    """Convert wiki markup to plain display text."""
    logger.debug("Converting wiki markup to text: %s", wiki_text)

    def replace_link(match):
        # Extract text from wiki links, taking the display text after '|' if present
        inner = match.group(1)
        if "|" in inner:
            return inner.split("|")[-1]  # Use text after last '|' as display text
        return inner  # Use entire inner text if no '|'

    # Pattern matches [[link]] or [[link|text]] without nested brackets
    pattern = r"\[\[([^\]\[]*)\]\]"
    return re.sub(pattern, replace_link, wiki_text)


def extract_words(translation_part):
    """Extract words from {{t...}} templates, handling [[...]] via wiki_to_text."""
    logger.debug("Extracting words from translation part: %s", translation_part)
    # Match templates like {{t|...}}, {{t+|...}}, or {{t-|...}}
    pattern = r"\{\{t[+-]?\|(.*?)\}\}"
    matches = re.findall(pattern, translation_part)
    words = []
    for match in matches:
        cleaned_match = wiki_to_text(match)
        params = cleaned_match.split("|")
        # Assume second parameter is the word (after language code)
        if len(params) >= 2:
            word = params[1].strip()
            if word:  # Only add non-empty words
                words.append(word)
    logger.debug("Extracted words: %s", words)
    return words


def remove_unmatched_brackets(phrase):
    """Remove unmatched brackets, parentheses, or braces."""
    pairs = {"]": "[", ")": "(", "}": "{"}
    opening = set(["[", "(", "{"])
    closing = set(["]", ")", "}"])

    stack = []
    unmatched = set()

    # Track positions of brackets to identify unmatched ones
    for i, char in enumerate(phrase):
        if char in opening:
            stack.append((char, i))
        elif char in closing:
            if stack and pairs[char] == stack[-1][0]:
                stack.pop()  # Matched pair found
            else:
                unmatched.add(i)  # Unmatched closing bracket

    # Add positions of unmatched opening brackets
    unmatched.update(i for _, i in stack)
    # Reconstruct phrase excluding unmatched bracket positions
    result = "".join(char for i, char in enumerate(phrase) if i not in unmatched)
    return result


def clean_phrase(phrase):
    """Clean a phrase by decoding HTML entities, removing brackets/quotes, and normalizing slashes and whitespace."""
    logger.debug("Cleaning phrase: %s", phrase)
    phrase = html.unescape(phrase)  # Decode HTML entities (e.g., &amp; to &)
    phrase = re.sub(
        r"\[\[(.*?)\]\]", r"\1", phrase
    )  # Remove wiki link brackets, keep inner text
    phrase = re.sub(r"''(.*?)''", r"\1", phrase)  # Remove double single quotes
    phrase = re.sub(r'"(.*?)"', r"\1", phrase)  # Remove double quotes
    phrase = remove_unmatched_brackets(phrase)  # Remove any unmatched brackets
    phrase = phrase.replace("/", " / ")  # Normalize slashes for alternative handling
    phrase = re.sub(r"\s+", " ", phrase)  # Normalize whitespace
    cleaned = phrase.strip()  # Remove leading/trailing whitespace
    logger.debug("Cleaned phrase: %s", cleaned)
    return cleaned


def generate_combinations(phrase):
    """Generate all possible phrase combinations, handling parentheses and '/' alternatives."""
    logger.debug("Generating combinations for phrase: %s", phrase)

    # Handle empty input
    if not phrase.strip():
        return []

    # Tokenize the phrase into words and parenthetical expressions
    def tokenize(phrase):
        tokens = []
        current_token = []
        level = 0

        for char in phrase:
            if char == "(":
                level += 1
                current_token.append(char)
            elif char == ")":
                level -= 1
                current_token.append(char)
            elif char.isspace() and level == 0:
                if current_token:
                    tokens.append("".join(current_token))
                    current_token = []
            else:
                current_token.append(char)

        if current_token:
            tokens.append("".join(current_token))

        return tokens

    def is_parenthetical(token):
        # Check if token is a standalone parenthetical like (word)
        return bool(re.fullmatch(r"\([^()]*\)", token))

    def is_attached_parenthetical(token):
        # Check if token has attached parenthetical like word(suffix) or (prefix)word
        return "(" in token and ")" in token and not is_parenthetical(token)

    def process_attached_parenthetical(token):
        # Process tokens like word(suffix) recursively
        results = []
        match = re.match(r"^([^()]*?)\(([^()]*?)\)(.*)$", token)
        if not match:
            return [token]  # Base case: no parenthetical

        prefix, content, suffix = match.groups()
        # Include the parenthetical content
        results.extend(process_attached_parenthetical(prefix + content + suffix))
        # Exclude the parenthetical content
        next_token = prefix + suffix
        if next_token and next_token != token:
            results.extend(process_attached_parenthetical(next_token))
        elif next_token:
            results.append(next_token)

        return list(dict.fromkeys(results))  # Remove duplicates

    def process_standalone_group(group):
        # Generate combinations for standalone parentheticals like (prefix) (suffix)
        if not group:
            return [""]
        contents = [t[1:-1] for t in group]  # Remove parentheses
        combinations = []
        for i in range(len(contents) + 1):
            suffix = " ".join(contents[i:]).strip()
            combinations.append(suffix)
        return [
            c for c in combinations if c or not combinations == [""]
        ]  # Handle empty cases

    def normalize_space(s):
        return " ".join(s.split())

    # Tokenize the phrase
    tokens = tokenize(phrase)

    # Process attached parentheticals like "word(suffix)"
    segments = []
    i = 0
    while i < len(tokens):
        if is_attached_parenthetical(tokens[i]):
            segments.append(process_attached_parenthetical(tokens[i]))
            i += 1
        elif is_parenthetical(tokens[i]):
            # Process standalone parentheticals like "(prefix) word"
            group = []
            while i < len(tokens) and is_parenthetical(tokens[i]):
                group.append(tokens[i])
                i += 1
            segments.append(process_standalone_group(group))
        else:
            segments.append([tokens[i]])  # Regular word
            i += 1

    # Generate all combinations of the segments
    intermediate_phrases = [
        " ".join(combo).strip() for combo in itertools.product(*segments)
    ]
    intermediate_phrases = [
        normalize_space(p) for p in intermediate_phrases if p.strip()
    ]

    # Handle slashes for alternatives
    final_combinations = set()
    for intermediate in intermediate_phrases:
        words = re.split(r"\s+", intermediate.strip())
        segments = []
        current_alternatives = []
        i = 0

        while i < len(words):
            if i + 1 < len(words) and words[i] == "/":
                i += 1
                continue
            if i > 0 and words[i - 1] == "/":
                current_alternatives.append(words[i])
                i += 1
                continue
            if current_alternatives:
                segments.append(current_alternatives)
                current_alternatives = []
            if i + 1 < len(words) and words[i + 1] == "/":
                current_alternatives.append(words[i])
                i += 2
                continue
            segments.append([words[i]])
            i += 1

        if current_alternatives:
            segments.append(current_alternatives)

        # Generate combinations for this intermediate phrase
        for combo in itertools.product(*segments):
            final_combinations.add(normalize_space(" ".join(combo)))

    # Finalize the combinations by sorting and removing duplicates
    result = sorted(list(final_combinations))
    return result


def process_file(lang1, lang2, input_file, output_file):
    """Process the input file to extract, clean, and sort dictionary entries."""
    logger.info(
        "Starting processing: lang1=%s, lang2=%s, input_file=%s, output_file=%s",
        lang1,
        lang2,
        input_file,
        output_file,
    )

    # Read the input file line by line
    word_pairs = []
    try:
        with open(input_file, "r", encoding="utf-8") as file:
            in_block = False
            lang1_words = set()
            lang2_words = set()
            line_count = 0

            # Extract word pairs from translation blocks
            for line in file:
                line_count += 1
                if line_count % 1000000 == 0:
                    logger.info("Processed %d lines", line_count)

                line = line.strip()
                if line.startswith("{{trans-top|"):
                    in_block = True
                    lang1_words = set()
                    lang2_words = set()
                    logger.debug("Entered translation block")
                    continue
                if line.startswith("{{trans-bottom}}"):
                    if in_block and lang1_words and lang2_words:
                        # Pair each word from lang1 with each word from lang2
                        for word1 in lang1_words:
                            for word2 in lang2_words:
                                word_pairs.append((word1, word2))
                        logger.debug(
                            "Extracted %d pairs from block",
                            len(lang1_words) * len(lang2_words),
                        )
                    in_block = False
                    lang1_words = set()
                    lang2_words = set()
                    continue
                if in_block:
                    cleaned_line = line.lstrip("* :")
                    if ":" in cleaned_line:
                        language_part, translation_part = cleaned_line.split(":", 1)
                        language = language_part.strip()
                        if language == lang1:
                            words = extract_words(translation_part)
                            lang1_words.update(words)
                            logger.debug("Found %s words: %s", lang1, words)
                        elif language == lang2:
                            words = extract_words(translation_part)
                            lang2_words.update(words)
                            logger.debug("Found %s words: %s", lang2, words)
        logger.info("Finished reading file: %d lines processed", line_count)
    except FileNotFoundError:
        logger.error("File not found: %s", input_file)
        sys.exit(1)
    except Exception as e:
        logger.error("Error extracting from file: %s", e)
        sys.exit(1)

    logger.info("Extracted %d word pairs", len(word_pairs))

    # Clean phrases and generate combinations for original phrases
    cleaned_pairs = []
    for original, translation in word_pairs:
        cleaned_original = clean_phrase(original)
        cleaned_translation = clean_phrase(translation)
        original_combinations = generate_combinations(cleaned_original)
        for comb in original_combinations:
            cleaned_pairs.append((comb, cleaned_translation))
    logger.info("Generated %d cleaned pairs", len(cleaned_pairs))

    # Sort the pairs and remove duplicates
    def sort_key(pair):
        original, translation = pair
        word_count = len(translation.split())
        char_count = len(translation)
        return (original, word_count, char_count, translation)

    sorted_pairs = sorted(set(cleaned_pairs), key=sort_key)
    logger.info("After sorting and deduplication: %d pairs", len(sorted_pairs))

    # Write the sorted pairs to the output file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for original, translation in sorted_pairs:
                f.write(f"{original}\t{translation}\n")
        logger.info("Successfully wrote output to %s", output_file)
    except Exception as e:
        logger.error("Error writing to output file: %s", e)
        sys.exit(1)


def run_tests():
    """Run the test cases for generate_combinations."""
    # fmt: off
    tests = [
        {
            "name": "Single Parenthetical",
            "input": "(zapato de) tenis",
            "expected": ["tenis", "zapato de tenis"]
        },
        {
            "name": "Multiple Parenthetical",
            "input": "(ser) (un) puro nervio",
            "expected": ["puro nervio", "un puro nervio", "ser un puro nervio"]
        },
        {
            "name": "Slash Alternatives",
            "input": "gato / felino",
            "expected": ["felino", "gato"]
        },
        {
            "name": "Parentheses with Slash",
            "input": "(avión de) caza / combate furtivo",
            "expected": ["caza furtivo", "avión de caza furtivo", "combate furtivo", "avión de combate furtivo"]
        },
        {
            "name": "Parentheses with Slash 2",
            "input": "(avión de) (caza / combate) furtivo",
            "expected": ["caza furtivo", "avión de caza furtivo", "combate furtivo", "avión de combate furtivo", "furtivo"]
        },
        {
            "name": "Multiple Slashes",
            "input": "(rojo / azul / verde) claro",
            "expected": ["azul claro", "rojo claro", "verde claro", "claro"]
        },
        {
            "name": "Multiple Slashes",
            "input": "rojo / azul / verde claro",
            "expected": ["azul claro", "rojo claro", "verde claro"]
        },
        {
            "name": "No Special Chars",
            "input": "casa grande",
            "expected": ["casa grande"]
        },
        {
            "name": "Empty Parentheses",
            "input": "() palabra",
            "expected": ["palabra"]
        },
        {
            "name": "Only Parenthetical",
            "input": "(opcional)",
            "expected": ["opcional"]
        },
        {
            "name": "Multiple Slashes",
            "input": "rojo / azul / verde claro",
            "expected": ["azul claro", "rojo claro", "verde claro"]
        },
        {
            "name": "Parentheses with Slashes Inside",
            "input": "(grande / pequeño) casa",
            "expected": ["casa", "grande casa", "pequeño casa"]
        },
        {
            "name": "Complex Case",
            "input": "(ser) (de) derecha / derechas / derecho / derechos",
            "expected": ["derecha", "derechas", "derecho", "derechos",
                         "de derecha", "de derechas", "de derecho", "de derechos",
                         "ser de derecha", "ser de derechas", "ser de derecho", "ser de derechos"]
        },
        {
            "name": "Whitespace Handling",
            "input": "(  zapato de  )   tenis  ",
            "expected": ["tenis", "zapato de tenis"]
        },
        {
            "name": "Non-Whitespace Handling 1",
            "input": "some(thing)one",
            "expected": ["someone", "somethingone"]
        },
        {
            "name": "Non-Whitespace Handling 2",
            "input": "amochiguar(se)",
            "expected": ["amochiguar", "amochiguarse"]
        },
        {
            "name": "Non-Whitespace Handling 3",
            "input": "(some)thing",
            "expected": ["something", "thing"]
        },
        {
            "name": "Non-Whitespace Handling 4",
            "input": "a(a)x(b)(c)",
            "expected": ["aax", "aaxb", "aaxbc", "aaxc", "ax", "axb", "axbc", "axc"]
        },
        {
            "name": "Non-Whitespace Handling 5",
            "input": "negar(se a)",
            "expected": ["negarse a", "negar"]
        },
        {
            "name": "Complex 1",
            "input": "a (b) (c / d) (e) f",
            "expected": ["a b c e f", "a b d e f", "a c e f", "a d e f", "a e f", "a f"]
        },
        {
            "name": "Complex 2",
            "input": "a (b) (c) d / e (f) g",
            "expected": ["a b c d f g", "a b c e f g", "a c d f g", "a c e f g", "a d f g", "a e f g",
                         "a b c d g", "a b c e g", "a c d g", "a c e g", "a d g", "a e g"]
        },
        {
            "name": "Empty Input",
            "input": "",
            "expected": []
        }
    ]
    # fmt: on

    for test in tests:
        name = test["name"]
        input_phrase = test["input"]
        expected = sorted(test["expected"])  # Ensure expected is sorted for comparison
        actual = generate_combinations(input_phrase)
        if actual == expected:
            print(f"Test '{name}' PASSED")
        else:
            print(f"Test '{name}' FAILED")
            print(f"Input: {input_phrase}")
            print(f"Expected: {expected}")
            print(f"Actual: {actual}")


if __name__ == "__main__":
    # Check command-line arguments and run the appropriate function
    if len(sys.argv) == 2 and sys.argv[1] == "--test":
        logger.info("Running test cases")
        run_tests()
    elif len(sys.argv) == 5:
        lang1 = sys.argv[1]
        lang2 = sys.argv[2]
        input_file = sys.argv[3]
        output_file = sys.argv[4]
        process_file(lang1, lang2, input_file, output_file)
    else:
        logger.error(
            "Invalid arguments.\n"
            "Usage: python convert_enwiktionary.py lang1 lang2 input_file output_file\n"
            "Example: python convert_enwiktionary.py Spanish German enwiktionary-20250420-pages-articles-multistream.xml dict_es-de.txt\n"
            "Or to run tests: python convert_enwiktionary.py --test"
        )
        sys.exit(1)
