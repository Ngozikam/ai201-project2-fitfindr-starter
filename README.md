# FitFindr

FitFindr is a multi-tool AI agent that helps a user find a secondhand clothing item, style it with their wardrobe, and generate a short shareable fit card. The agent uses a planning loop, stores intermediate results in a session dictionary, and stops early when a failure occurs.

## How to Run

```bash
pip install -r requirements.txt

Create a .env file in the project root:

Bash
GROQ_API_KEY=your_groq_api_key_here

Run the app:
python app.py

Open the local URL shown in the terminal, usually:
http://localhost:7860

## Tool Inventory

** Tool 1: search_listings(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]

Purpose: Searches the mock marketplace dataset for secondhand clothing listings that match the user's requested item, optional size, and optional maximum price.

Inputs:

description (str): Search keywords such as "vintage graphic tee".
size (str | None): Optional size filter such as "M" or "XXS". If None, size filtering is skipped.
max_price (float | None): Optional maximum price. If None, price filtering is skipped.

Output: Returns a list of listing dictionaries sorted by relevance. Each listing contains id, title, description, category, style_tags, size, condition, price, colors, brand, and platform. If no listings match, it returns [].

** Tool 2: suggest_outfit(new_item: dict, wardrobe: dict) -> str

Purpose: Suggests 1–2 outfits using the selected thrifted item and the user's wardrobe.

Inputs:

new_item (dict): The listing selected by the agent.
wardrobe (dict): A wardrobe dictionary with an items list.

Output: Returns a non-empty outfit suggestion string. If the wardrobe has items, the suggestion uses named wardrobe pieces. If the wardrobe is empty, it returns general styling advice instead of crashing.

** Tool 3: create_fit_card(outfit: str, new_item: dict) -> str

Purpose: Creates a short social-media-style caption for the thrifted outfit.

Inputs:

outfit (str): The outfit suggestion returned by suggest_outfit().
new_item (dict): The selected listing dictionary.

Output: Returns a 2–4 sentence fit card caption mentioning the item, price, platform, and outfit vibe. If the outfit string is empty or missing, it returns a descriptive error message.

## Planning Loop

The planning loop is implemented in run_agent() in agent.py.

The loop works as follows:

A new session dictionary is created for the user query.
The query is parsed into description, size, and max_price.
The agent calls search_listings(description, size, max_price).
If no listings are returned, the agent stores an error message in session["error"] and returns early. It does not call suggest_outfit() or create_fit_card().
If listings are found, the agent stores the top result as session["selected_item"].
The selected item and wardrobe are passed into suggest_outfit().
The outfit suggestion is stored as session["outfit_suggestion"].
The outfit suggestion and selected item are passed into create_fit_card().
The fit card is stored as session["fit_card"].
The completed session is returned.

The agent does not call all tools unconditionally. It branches after the search step and stops if there are no results.

## State Management

FitFindr uses a session dictionary as the single source of truth for one interaction.

The session stores:

query: original user query
parsed: extracted search parameters
search_results: results from search_listings()
selected_item: top listing selected by the agent
wardrobe: selected wardrobe
outfit_suggestion: result from suggest_outfit()
fit_card: result from create_fit_card()
error: error message if the workflow stops early

State flows from tool to tool. The selected listing from search_listings() is passed directly into suggest_outfit(). The outfit suggestion from suggest_outfit() is passed directly into create_fit_card(). The user does not need to re-enter the selected item or outfit.

## Error Handling
Tool	Failure Mode	Agent Response
search_listings	No listings match the query, size, or budget.	Returns []. The planning loop sets session["error"] with a helpful message and stops before calling the other tools.
suggest_outfit	Wardrobe is empty.	Returns general styling advice for the selected item instead of crashing.
create_fit_card	Outfit string is empty or missing.	Returns a descriptive error message explaining that an outfit recommendation is required first.
Concrete Failure Examples

I tested search_listings() with an impossible query:

python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"

It returned:

[]

I also tested the full agent with the same impossible query:

python -c "from agent import run_agent; from utils.data_loader import get_example_wardrobe; s=run_agent('designer ballgown size XXS under $5', get_example_wardrobe()); print(s['error']); print(s['fit_card'])"

It returned:

No matching listings were found. Try broadening your search, changing the size, increasing your budget, or using fewer specific keywords.
None

This confirmed that the agent stopped early and did not create a fit card.

I tested suggest_outfit() with get_empty_wardrobe() and confirmed that it returned general styling advice. I also tested create_fit_card("", item) and confirmed that it returned an error message instead of raising an exception.

## Spec Reflection

One way the spec helped me was by requiring each tool to be implemented and tested independently before connecting them through the agent. This made debugging easier because I could confirm each tool worked before wiring the planning loop.

One implementation divergence is that I used simple regular expressions to parse size and price from the query instead of using an LLM parser. I chose this because the expected query patterns were simple, such as "size M" and "under $30", and regex made the planning loop easier to test and explain.

## AI Usage Transparency

I used AI assistance in specific parts of the project.

First, I used AI to help implement the three required tool functions in tools.py. I provided the Tool Inventory sections from planning.md, including the function names, input parameters, return values, and failure modes. I reviewed the generated code to make sure search_listings() used load_listings(), suggest_outfit() handled an empty wardrobe, and create_fit_card() guarded against an empty outfit string.

Second, I used AI to help implement the planning loop in agent.py. I provided the Planning Loop, State Management section, and architecture diagram from planning.md. I reviewed the generated logic to ensure that it branched when search_listings() returned no results, stored values in the session dictionary, and did not call all three tools unconditionally.

Third, I used AI to help write pytest tests in tests/test_tools.py. I checked that the tests matched the actual function signatures and verified the required failure modes. I then ran:

python -m pytest tests/

and confirmed that all seven tests passed.

Testing Summary

The project includes tests in tests/test_tools.py.

The tests verify that:

search_listings() returns results for a valid query.
search_listings() returns [] for an impossible query.
search_listings() respects the price filter.
suggest_outfit() returns a non-empty string with the example wardrobe.
suggest_outfit() returns a non-empty string with an empty wardrobe.
create_fit_card() returns a caption for valid input.
create_fit_card() returns an error message for an empty outfit string.

All tests passed:

7 passed

## Demo Video
The demo video shows:

A happy-path query: vintage graphic tee under $30.

A full flow from listing search to outfit suggestion to fit card.

Narration of which tool is called at each step.

Explanation of how selected_item and outfit_suggestion pass through the session state.

A failure case: designer ballgown size XXS under $5, showing the agent's graceful error response.

Demo link: https://drive.google.com/file/d/1BpSPUKXIJGGV8NO-bi2ga8ZXHafzfv0M/view?usp=sharing