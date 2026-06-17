"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    # Replace this with your implementation
    listings = load_listings()

    if not description or not description.strip():
        return []

    query_terms = description.lower().replace("-", " ").split()
    results = []

    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue

        if size:
            requested_size = size.lower()
            listing_size = listing["size"].lower()
            if requested_size not in listing_size:
                continue

        searchable_text = " ".join([
            listing.get("title", ""),
            listing.get("description", ""),
            listing.get("category", ""),
            " ".join(listing.get("style_tags", [])),
            " ".join(listing.get("colors", [])),
            str(listing.get("brand") or ""),
            listing.get("platform", ""),
        ]).lower().replace("-", " ")

        score = sum(1 for term in query_terms if term in searchable_text)

        if score > 0:
            results.append((score, listing))

    results.sort(key=lambda item: item[0], reverse=True)

    return [listing for score, listing in results]
    


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # Replace this with your implementation
    client = _get_groq_client()

    wardrobe_items = wardrobe.get("items", [])

    item_summary = f"""
Title: {new_item.get("title", "Unknown item")}
Description: {new_item.get("description", "")}
Category: {new_item.get("category", "")}
Style tags: {", ".join(new_item.get("style_tags", []))}
Colors: {", ".join(new_item.get("colors", []))}
Price: ${new_item.get("price", "")}
Platform: {new_item.get("platform", "")}
"""

    if not wardrobe_items:
        prompt = f"""
The user has no saved wardrobe items yet.

Suggest 1–2 general outfit ideas for this thrifted item.

Recommend clothing pieces that would pair well with it, describe the overall style or vibe, and explain why the combination works.

Thrifted item:
{item_summary}

Keep the response friendly, practical, and concise.
"""
    else:
        wardrobe_summary = "\n".join(
            f"- {item.get('name', 'Unnamed item')} "
            f"({item.get('category', '')}; "
            f"colors: {', '.join(item.get('colors', []))}; "
            f"style: {', '.join(item.get('style_tags', []))}; "
            f"notes: {item.get('notes') or 'none'})"
            for item in wardrobe_items
        )

        prompt = f"""
Suggest 1–2 complete outfits using the thrifted item and specific named pieces from the user's wardrobe.

Thrifted item:
{item_summary}

User wardrobe:
{wardrobe_summary}

Mention the wardrobe item names naturally and explain why they work well together.

Keep the response friendly, practical, and concise.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.8,
    )

    outfit_text = response.choices[0].message.content.strip()

    if not outfit_text:
        return (
            "I could not generate an outfit suggestion right now. "
            "Please try again with another item or wardrobe."
        )

    return outfit_text
    


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Replace this with your implementation
    if not outfit or not outfit.strip():
        return (
            "Unable to create a fit card because the outfit recommendation is "
            "missing or incomplete. Please generate an outfit suggestion first."
        )

    client = _get_groq_client()

    prompt = f"""
Create a 2–4 sentence Instagram/TikTok style caption for a thrifted outfit.

Requirements:
- Sound casual, authentic, and fun.
- Mention the item name exactly once.
- Mention the price exactly once.
- Mention the platform exactly once.
- Capture the outfit vibe using the outfit description.
- Do not sound like an advertisement.

Item Details:
Title: {new_item.get("title", "Unknown item")}
Price: ${new_item.get("price", "")}
Platform: {new_item.get("platform", "")}

Outfit Suggestion:
{outfit}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=1.0,
    )

    fit_card = response.choices[0].message.content.strip()

    if not fit_card:
        return (
            "I could not generate a fit card right now. "
            "Please try again."
        )

    return fit_card
    
