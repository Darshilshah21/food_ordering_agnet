from functools import lru_cache
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Optional

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from sqlalchemy import select

from backend.config import get_settings
from backend.agent.prompts import SYSTEM_PROMPT
from backend.agent.tools import (
    TOOLS,
    CURRENT_USER_ID,
    create_food_order,
)
from backend.database.database_in import SessionLocal
from backend.database.models import MenuItem
from backend.services.order_service import ALIASES


@lru_cache
def get_agent_executor() -> AgentExecutor:
    settings = get_settings()

    llm = ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, TOOLS, prompt)

    return AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=False,
        max_iterations=8,
        handle_parsing_errors=True,
    )


# ---------------------------------------------------------------------------
# NUMBER / QUANTITY HANDLING
# ---------------------------------------------------------------------------

_NUMBER_WORDS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "couple": 2,
    "pair": 2,
    "dozen": 12,
}


# These phrases are converted before quantity extraction.
_QUANTITY_PHRASES = {
    "half a dozen": "6",
    "half dozen": "6",
    "a couple of": "2",
    "couple of": "2",
    "a pair of": "2",
    "pair of": "2",
}


# ---------------------------------------------------------------------------
# ORDER / INFORMATION INTENT
# ---------------------------------------------------------------------------

_ORDER_WORDS_PATTERN = re.compile(
    r"\b("
    r"order|ordering|buy|purchase|"
    r"get|add|place|want|"
    r"give me|book|take|"
    r"i'll have|ill have|"
    r"can i have|"
    r"i would like|"
    r"i'd like"
    r")\b",
    re.IGNORECASE,
)


_INFORMATION_PATTERN = re.compile(
    r"\b("
    r"show|list|display|view|"
    r"price|prices|cost|"
    r"how much|"
    r"what|which|"
    r"tell me|"
    r"describe|description|"
    r"ingredient|ingredients|"
    r"available|availability|"
    r"menu|"
    r"recommend|recommendation|"
    r"suggest|"
    r"calorie|calories|"
    r"contains|"
    r"do you have|"
    r"is there"
    r")\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# TEXT NORMALIZATION
# ---------------------------------------------------------------------------

def _normalize_text(value: str) -> str:
    
    value = unicodedata.normalize("NFKC", str(value))
    value = value.lower()

    # Convert common punctuation to spaces.
    value = re.sub(r"[-_/]", " ", value)

    # Keep alphanumeric characters and spaces.
    value = re.sub(r"[^a-z0-9\s]", " ", value)

    # Collapse repeated spaces.
    value = re.sub(r"\s+", " ", value).strip()

    return value


def _normalize_token(token: str) -> str:
    
    token = _normalize_text(token)

    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"

    if token.endswith("es") and len(token) > 4:
        # boxes -> box
        # fries is handled separately by fuzzy matching.
        return token[:-2]

    if token.endswith("s") and len(token) > 3:
        return token[:-1]

    return token


def _tokenize(value: str) -> list[str]:
    return [
        _normalize_token(x)
        for x in _normalize_text(value).split()
        if x
    ]


# ---------------------------------------------------------------------------
# MENU LOADING
# ---------------------------------------------------------------------------

def _get_available_menu() -> list[MenuItem]:
   
    db = SessionLocal()

    try:
        return db.scalars(
            select(MenuItem)
            .where(MenuItem.is_available.is_(True))
            .order_by(MenuItem.id)
        ).all()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# FUZZY MENU MATCHING
# ---------------------------------------------------------------------------

def _token_similarity(requested: str, candidate: str) -> float:
    
    requested_tokens = _tokenize(requested)
    candidate_tokens = _tokenize(candidate)

    if not requested_tokens or not candidate_tokens:
        return 0.0

    # Each requested token gets its best matching candidate token.
    requested_scores = []

    for requested_token in requested_tokens:
        best = max(
            SequenceMatcher(
                None,
                requested_token,
                candidate_token,
            ).ratio()
            for candidate_token in candidate_tokens
        )
        requested_scores.append(best)

    requested_to_candidate = sum(requested_scores) / len(requested_scores)

    # Also measure how much of the candidate phrase is covered by the
    # requested phrase.
    candidate_scores = []

    for candidate_token in candidate_tokens:
        best = max(
            SequenceMatcher(
                None,
                candidate_token,
                requested_token,
            ).ratio()
            for requested_token in requested_tokens
        )
        candidate_scores.append(best)

    candidate_to_requested = sum(candidate_scores) / len(candidate_scores)

    # Requested phrase coverage is slightly more important.
    score = (
        requested_to_candidate * 0.65
        + candidate_to_requested * 0.35
    )

    return score


def _build_menu_variants(menu_items: list[MenuItem],) -> list[tuple[str, str]]:
    
    available_names = {
        _normalize_text(item.name): item.name
        for item in menu_items
    }

    variants: list[tuple[str, str]] = []

    # Canonical menu names.
    for normalized_name, canonical_name in available_names.items():
        variants.append(
            (normalized_name, canonical_name)
        )

    # Known aliases.
    for alias, target in ALIASES.items():
        normalized_alias = _normalize_text(alias)
        normalized_target = _normalize_text(target)

        if normalized_target in available_names:
            variants.append(
                (
                    normalized_alias,
                    available_names[normalized_target],
                )
            )

    # Remove duplicates while preserving order.
    unique = []
    seen = set()

    for variant, canonical in variants:
        key = (variant, canonical)

        if key not in seen:
            seen.add(key)
            unique.append((variant, canonical))

    return unique


def _best_menu_match(requested_text: str,menu_items: list[MenuItem],) -> tuple[Optional[str], Optional[list[str]]]:
    
    requested = _normalize_text(requested_text)

    if not requested:
        return None, None

    variants = _build_menu_variants(menu_items)

    # -----------------------------------------------------------------------
    # 1. Exact canonical / alias match
    # -----------------------------------------------------------------------

    exact_matches = [
        canonical
        for variant, canonical in variants
        if variant == requested
    ]

    if exact_matches:
        return exact_matches[0], None

    # -----------------------------------------------------------------------
    # 2. Fuzzy match
    # -----------------------------------------------------------------------

    scores_by_canonical: dict[str, float] = {}

    for variant, canonical in variants:
        score = _token_similarity(requested, variant)

        previous = scores_by_canonical.get(canonical, 0.0)

        if score > previous:
            scores_by_canonical[canonical] = score

    if not scores_by_canonical:
        return None, None

    ranked = sorted(
        scores_by_canonical.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    best_name, best_score = ranked[0]

    # A score below this is too weak to be treated as a food item.
    MATCH_THRESHOLD = 0.68

    if best_score < MATCH_THRESHOLD:
        return None, None

    if len(ranked) > 1:
        second_name, second_score = ranked[1]

        if (
            second_score >= MATCH_THRESHOLD
            and best_score - second_score < 0.08
        ):
            return None, [
                best_name,
                second_name,
            ]

    return best_name, None


# ---------------------------------------------------------------------------
# QUANTITY EXTRACTION
# ---------------------------------------------------------------------------

_QUANTITY_TOKEN_PATTERN = (
    r"(?:"
    r"\d+|"
    r"a|an|"
    r"one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|"
    r"sixteen|seventeen|eighteen|nineteen|twenty|"
    r"couple|pair|dozen"
    r")"
)

_QUANTITY_REGEX = re.compile(
    rf"\b({_QUANTITY_TOKEN_PATTERN})\b",
    re.IGNORECASE,
)


def _quantity_from_token(token: str) -> int:
    token = token.lower().strip()

    if token.isdigit():
        return int(token)

    return _NUMBER_WORDS[token]


def _prepare_quantity_phrases(text: str) -> str:
    """
    Convert phrases such as:

        half dozen -> 6
        a couple of -> 2
        a pair of -> 2
    """
    normalized = _normalize_text(text)

    # Longest first.
    for phrase, replacement in sorted(
        _QUANTITY_PHRASES.items(),
        key=lambda x: len(x[0]),
        reverse=True,
    ):
        normalized = normalized.replace(
            phrase,
            replacement,
        )

    return normalized


# ---------------------------------------------------------------------------
# ITEM PHRASE CLEANING
# ---------------------------------------------------------------------------

def _clean_item_phrase(value: str) -> str:
    """
    Remove common natural-language words around an item.

    Example:

        "burger please"
        -> "burger"

        "and margi pizza"
        -> "margi pizza"
    """
    value = _normalize_text(value)

    removable_words = {
        "please",
        "pls",
        "plz",
        "kindly",
        "the",
        "some",
        "of",
        "for",
        "me",
    }

    tokens = value.split()

    # Remove leading noise.
    while tokens and tokens[0] in removable_words:
        tokens.pop(0)

    # Remove trailing noise.
    while tokens and tokens[-1] in removable_words:
        tokens.pop()

    # "and" is useful as a separator but not part of a menu name.
    while tokens and tokens[0] in {"and", "plus"}:
        tokens.pop(0)

    while tokens and tokens[-1] in {"and", "plus"}:
        tokens.pop()

    return " ".join(tokens)


# ---------------------------------------------------------------------------
# QUANTITY + ITEM PARSER
# ---------------------------------------------------------------------------

def _extract_quantity_based_items(text: str,menu_items: list[MenuItem],):
   
    prepared = _prepare_quantity_phrases(text)

    matches = list(_QUANTITY_REGEX.finditer(prepared))

    if not matches:
        return None

    items = []

    for index, match in enumerate(matches):
        quantity_token = match.group(1)
        quantity = _quantity_from_token(quantity_token)

        if quantity <= 0:
            return {
                "items": None,
                "clarification": (
                    "Please provide a quantity greater than zero."
                ),
            }

        if quantity > 50:
            return {
                "items": None,
                "clarification": (
                    f"The quantity {quantity} is too large. "
                    "Please order a maximum of 50 of one item."
                ),
            }

        # The item text begins immediately after the quantity.
        item_start = match.end()

        # The item text ends immediately before the next quantity.
        if index + 1 < len(matches):
            item_end = matches[index + 1].start()
        else:
            item_end = len(prepared)

        item_text = prepared[item_start:item_end]

        # Remove separators / punctuation-like text.
        item_text = item_text.strip(" ,;:-")

        item_text = _clean_item_phrase(item_text)

        if not item_text:
            return {
                "items": None,
                "clarification": (
                    "I found a quantity but could not identify the "
                    "food item after it. Please specify the item."
                ),
            }

        canonical_name, ambiguous = _best_menu_match(item_text,menu_items,)

        if ambiguous:
            options = " or ".join(ambiguous)

            return {
                "items": None,
                "clarification": (
                    f"I understood that you want {quantity} "
                    f"of '{item_text}', but that could mean "
                    f"{options}. Which one would you like?"
                ),
            }

        if canonical_name is None:
            return {
                "items": None,
                "clarification": (
                    f"I couldn't confidently identify '{item_text}' "
                    "from the current menu. Please provide the menu "
                    "item name."
                ),
            }

        items.append({"item": canonical_name,"quantity": quantity,})

    if not items:
        return None

    return {
        "items": items,
        "clarification": None,
    }


# ---------------------------------------------------------------------------
# NO-QUANTITY ITEM PARSER
# ---------------------------------------------------------------------------

def _find_menu_mentions_without_quantity(text: str,menu_items: list[MenuItem],):
    normalized = _normalize_text(text)

    tokens = normalized.split()

    if not tokens:
        return []

    variants = _build_menu_variants(menu_items)

    # Maximum number of words in any known menu variant.
    max_variant_words = max(len(variant.split())for variant, _ in variants)

    candidates = []

    for start in range(len(tokens)):
        for length in range(1,min(max_variant_words + 2, len(tokens) - start + 1),):
            end = start + length

            phrase = " ".join(tokens[start:end])

            canonical_name, ambiguous = _best_menu_match(phrase,menu_items,)

            if canonical_name is None:
                continue

            # Recalculate the best score so we can reject weak matches.
            canonical_variants = [
                variant
                for variant, canonical in variants
                if canonical == canonical_name
            ]

            best_score = max(
                _token_similarity(phrase, variant)
                for variant in canonical_variants
            )

            # No-quantity matching should be slightly more conservative.
            if best_score < 0.78:
                continue

            candidates.append({
                "start": start,
                "end": end,
                "item": canonical_name,
                "score": best_score,
            })

    if not candidates:
        return []

    candidates.sort(key=lambda x: (x["score"],x["end"] - x["start"],-x["start"],),reverse=True,)

    selected = []

    occupied_ranges = []

    for candidate in candidates:
        start = candidate["start"]
        end = candidate["end"]

        overlaps = any(
            start < existing_end
            and end > existing_start
            for existing_start, existing_end in occupied_ranges
        )

        if overlaps:
            continue

        selected.append(candidate)
        occupied_ranges.append((start, end))

    selected.sort(key=lambda x: x["start"])

    # Merge duplicate mentions if necessary.
    result = []

    for candidate in selected:
        result.append({"item": candidate["item"],"quantity": 1,})

    return result


# ---------------------------------------------------------------------------
# MAIN DIRECT ORDER EXTRACTION
# ---------------------------------------------------------------------------

def _extract_direct_order(message: str):
    
    if not message or not message.strip():
        return None

    text = _normalize_text(message)

    if _INFORMATION_PATTERN.search(text):
        return None

    menu_items = _get_available_menu()

    if not menu_items:
        return {
            "clarification": (
                "The menu is currently empty or unavailable."
            )
        }

    quantity_result = _extract_quantity_based_items(text,menu_items,)

    if quantity_result is not None:
        if quantity_result.get("clarification"):
            return quantity_result

        if quantity_result.get("items"):
            return quantity_result

    has_order_intent = bool(_ORDER_WORDS_PATTERN.search(text))

    menu_mentions = _find_menu_mentions_without_quantity(text,menu_items,)

    if menu_mentions:
        return {"items": menu_mentions}

    if has_order_intent:
        return {
            "clarification": (
                "I understood that you want to place an order, "
                "but I could not identify the requested menu item. "
                "Please provide the food or drink name."
            )
        }
    return None


# ---------------------------------------------------------------------------
# DIRECT ORDER EXECUTION
# ---------------------------------------------------------------------------

def _run_direct_order(items: list[dict]) -> str:
    return str(create_food_order.invoke({"items": items}))


# ---------------------------------------------------------------------------
# RESPONSE FORMATTER
# ---------------------------------------------------------------------------

def _format_created_order(result: str) -> str:
    lines = result.splitlines()

    if not lines:
        return result

    first = lines[0]

    try:
        order_id = first.split("id=",1,)[1].split()[0]

        total = first.split("total=",1,)[1]

        item_lines = "\n".join(lines[1:])

        return (
            f"Order #{order_id} confirmed.\n"
            f"{item_lines}\n"
            f"Total: {total}"
        )

    except (IndexError, ValueError):
        # Never break the response if the tool format changes slightly.
        return result


def run_agent(message: str,user_id: str = "default-user",) -> str:

    token = CURRENT_USER_ID.set(str(user_id or "default-user")[:100])

    try:
        direct_result = _extract_direct_order(message)

        if direct_result and direct_result.get("items"):
            result = _run_direct_order(direct_result["items"])

            if result.startswith("ORDER_CREATED"):
                return _format_created_order(result)

            if result.startswith("ORDER_NOT_CREATED"):
                return (
                    "I couldn't place that order because the requested "
                    f"items could not be validated against the current "
                    f"menu.\n{result}"
                )

            return result

        if (direct_result and direct_result.get("clarification")):
            return direct_result["clarification"]

        result = get_agent_executor().invoke({"input": message})

        return str(result.get("output", "")).strip()

    finally:
        CURRENT_USER_ID.reset(token)