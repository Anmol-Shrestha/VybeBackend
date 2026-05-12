'''
This request is for GET /restaurants/filter

Initial App Loading: 
An incomplete filter : userid + location

Get the first batch of restaurant: 
A complete filter : userid + location + filter



'''

# After the API Layer standardizes, normalizes, and pre-processes the data so that it is compatible with the service.
## This is what it is supposed to look like.
incomplete_filter = [
     {
        "name": "Mr.Vegan",
        "userID":123123,
        "latitude": 43.77579,
        "longitude": -79.20664,
        "dietary": [],
        "allergen":[],
        "cuisine":[],
        "meal_type":[],
        "price_max":30,
        "min_rating":4,
        "min_capacity":4,
        "has_parking":True,
        "live_music": True,
    },
]

complete_filter = [
    {
        "name": "Mr.Vegan",
        "userID":123123,
        "latitude": 43.77579,
        "longitude": -79.20664,
        "dietary": ['vegan'],
        "allergen":["nut, dairy, gluten"],
        "cuisine":[],
        "meal_type":[],
        "price_max":30,
        "min_rating":4,
        "min_capacity":4,
        "has_parking":True,
        "live_music": True,
    },
    
]
