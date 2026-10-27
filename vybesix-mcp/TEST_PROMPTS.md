# VybeSix MCP Test Prompts

Prompts for checking that the VybeSix MCP tools return the right results for each filter.

Each prompt is written the way a user would type it. Do not name a tool in the prompt. Claude should choose the tool itself, and you record which one it used.

## Setup

1. Start the backend (`backend/`, port 8000) and confirm it can reach MongoDB Atlas.
2. Confirm the MCP server is connected. In Claude Code, run `/mcp`. You should see `vybesix-mcp` with 4 tools: `search_restaurants_manual`, `search_restaurants_vector`, `search_food_manual`, `search_food_vector`.
3. Start a new chat for each prompt so earlier results don't affect the next one.

## How to record a run

For each prompt, record:

| Prompt | Tool Claude used | Results valid? | Notes |
|---|---|---|---|
| 1.1 | | | |

- **Tool used:** the tool Claude called (shown in the tool-call log).
- **Results valid:** every returned item meets the request. One item that breaks the filter is a fail.
- **Errors:** any `success: false`, 500 or connection error is a fail. Copy the error text into Notes.

## Expected results

These are for the person checking the results, not for the prompt.

Restaurants within 10 km of downtown Toronto (43.6532, -79.3832) that are tagged vegan: restaurant_3 (Purely Vegan Hub), restaurant_9 (The Cozy Study Cafe), restaurant_11 (Spice & Rhythm Indian Kitchen), restaurant_13 (Green Garden Bistro), restaurant_19 (Bubble Tea Paradise), restaurant_21 (Tropical Smoothie Bowl Café).

Restaurants tagged vegan but outside 10 km: restaurant_1 (24hr Vegan Diner, about 19.7 km) and restaurant_2 (Vegan Kitchen, about 19.4 km).

A restaurant can be tagged vegan and vegetarian at the same time. Results include restaurants tagged vegan even when they also list vegetarian. That is expected behavior, not a bug.

Other tags in the data:
- halal: restaurant_6 (Sultan's Halal Kitchen)
- kosher: restaurant_7 (The Kosher Deli)
- gluten free: restaurant_8, 17, 21
- live music: restaurant_3, 4, 5, 8, 11, 13, 18
- parking and live music: restaurant_3, 4, 5, 8, 18 (4 and 5 are in Scarborough, outside 10 km of downtown)
- Italian cuisine: restaurant_4 (The Green Leaf Bistro), restaurant_14 (Family Feast Pizzeria)

Food allergens in the data: coconut, dairy, eggs, gluten, nuts, peanuts, seafood, sesame, soy.

Notes:
- Prices are in dollars. Restaurant `price_max` is the restaurant's maximum price (from $8 to $100), and a search with a budget returns only restaurants at or under it. Food `price` is the dish price (from $4.50 to $65).
- Restaurant results can change with the time of day, because opening hours are applied.

---

## 1. Restaurants

### 1.1 Vegan restaurants nearby
> I'm downtown Toronto at 43.6532, -79.3832. Find me vegan restaurants within 10 km.

**Expected:** only restaurants tagged vegan, all within 10 km (see the expected list above).

### 1.2 Halal
> Find halal restaurants within 10 km of 43.6532, -79.3832.

**Expected:** only Sultan's Halal Kitchen.

### 1.3 Kosher
> Are there kosher restaurants within 10 km of 43.6532, -79.3832?

**Expected:** only The Kosher Deli.

### 1.4 Gluten-free
> I need gluten-free places within 10 km of 43.6532, -79.3832.

**Expected:** only restaurant_8, 17 and 21.

### 1.5 Parking and live music
> Show me restaurants within 10 km of 43.6532, -79.3832 that have both parking and live music.

**Expected:** within 10 km of downtown, only Purely Vegan Hub (restaurant_3), Sky & Stars Rooftop Lounge (restaurant_8) and The Jazz Corner Bar & Grill (restaurant_18). Restaurants 4 and 5 also have both, but they are in Scarborough, about 17 km away, so they should be excluded. Every result has both flags set to true.

### 1.6 Italian
> Find Italian restaurants within 10 km of 43.6532, -79.3832.

**Expected:** The Green Leaf Bistro and Family Feast Pizzeria.

### 1.7 Vegan with live music
> I'm vegan and want somewhere with live music within 10 km of 43.6532, -79.3832.

**Expected:** Purely Vegan Hub (restaurant_3), Spice & Rhythm Indian Kitchen (restaurant_11) and Green Garden Bistro (restaurant_13). Other vegan restaurants should be excluded.

### 1.8 Radius
> Find vegan restaurants within 1 km of 43.6532, -79.3832. Then do the same for 10 km. How do the lists compare?

**Expected:** the 10 km list contains the 1 km list, and no result is outside the radius.

### 1.9 Stored preferences
> My user ID is Mr.Vegan. Find restaurants near 43.6532, -79.3832 that match my stored preferences.

**Expected:** results match the user's stored dietary preference (vegan in the test data). Check that the user ID is correct before reading the result.

### 1.10 Semantic restaurant request
> Find a cozy vegan restaurant with live music near downtown Toronto.

**Expected:** Claude may first find vegan restaurants near downtown and then rank them by the description. Good candidates are Purely Vegan Hub, Green Garden Bistro and Spice & Rhythm Indian Kitchen. Note which tools Claude used.

### 1.10b Budget
> Find restaurants within 10 km of 43.6532, -79.3832 where I can spend no more than $12.

**Expected:** exactly two restaurants: Bubble Tea Paradise (restaurant_19, maximum $8) and Street Tacos Express (restaurant_16, maximum $12). No result should have a maximum above $12.

### 1.11 Ranking check (project spec)
> Between 24hr Vegan Diner and Purely Vegan Hub, which one should I go to for vegan food?

**Expected:** Purely Vegan Hub should rank first, as the project spec requires. Note how Claude got the answer.

---

## 2. Food

### 2.1 Vegan food at a restaurant
> What vegan dishes does 24hr Vegan Diner have?

**Expected:** only dishes tagged vegan at restaurant_1.

### 2.2 Peanut allergy
> I'm allergic to peanuts. What can I eat at 24hr Vegan Diner?

**Expected:** no dish with peanuts in its allergens. Midnight Pad Thai should be excluded.

This is the query that failed before the `allergens` filter was added to the food index. It should work now.

### 2.3 Several allergies
> I can't have soy or sesame. What vegan food is at 24hr Vegan Diner or Purely Vegan Hub?

**Expected:** no dish with soy or sesame in its allergens.

### 2.3b Budget for dishes
> What vegan dishes at 24hr Vegan Diner or Purely Vegan Hub cost under $8?

**Expected:** only dishes with `price` at or under 8. Crispy Tofu Fries ($6.99) and Vegan Dumplings ($7.50) should appear if they are at these restaurants.

### 2.4 Dessert
> Show me desserts at Bubble Tea Paradise.

**Expected:** only dessert items from restaurant_19.

### 2.5 Vegan dessert without nuts
> I'm vegan and allergic to nuts. Find vegan desserts at Bubble Tea Paradise, Tropical Smoothie Bowl Café or The Cozy Study Cafe.

**Expected:** only vegan desserts, with no nuts in their allergens.

### 2.6 Breakfast
> What breakfast food is at 24hr Vegan Diner?

**Expected:** only items with breakfast in their meal types.

### 2.7 Spice level
> What's the spiciest food at Spice & Rhythm Indian Kitchen?

**Expected:** results with the highest spice levels for restaurant_11. Note which spice level the results show.

### 2.8 Gluten-free food
> I need gluten-free food at Sky & Stars Rooftop Lounge, The Gluten-Free Haven or Tropical Smoothie Bowl Café.

**Expected:** only gluten-free items.

### 2.9 Mood-based food search
> I want something cozy and warm to eat tonight, like a comforting noodle soup.

**Expected:** a semantic result, such as 24-Hour Buddha Noodle Soup. Note which tools Claude used.

### 2.10 Food at a restaurant, described loosely
> Is there anything fresh and light at Tropical Smoothie Bowl Café?

**Expected:** items from restaurant_21 that match the description, such as smoothie bowls.

---

## 3. Vague requests

### 3.1 No location
> Recommend a good restaurant.

**Expected:** Claude asks for a location or preferences, or makes a reasonable default and says so.
