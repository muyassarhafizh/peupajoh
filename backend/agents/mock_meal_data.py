"""
Mock meal data for testing the nutrition advisor agent
"""

from models.models import NutritionInfo, FoodCategory

# Mock data with proper NutritionInfo objects
mock_meal_data = {
    'Breakfast': [
        {
            'id': 'BF001',
            'name': 'Scrambled Eggs',
            'local_name': 'Telur Orak-arik',
            'category': FoodCategory.PROTEIN,
            'subcategory': 'Eggs',
            'nutrition_per_100g': NutritionInfo(
                calories=149,
                protein=9.9,
                carbohydrates=1.6,
                fat=11.2,
                fiber=0,
                sugar=1.3,
                sodium=142
            ),
            'standard_portions': {'serving_size': 100, 'unit': 'grams'},
            'variations': ['with cheese', 'with vegetables'],
            'tags': ['eggs', 'breakfast', 'protein'],
            'is_composite': False,
            'embeddings': None
        }
    ],
    'Lunch': [
        {
            'id': 'LN001',
            'name': 'Grilled Chicken Breast',
            'local_name': 'Dada Ayam Panggang',
            'category': FoodCategory.PROTEIN,
            'subcategory': 'Poultry',
            'nutrition_per_100g': NutritionInfo(
                calories=165,
                protein=31.0,
                carbohydrates=0,
                fat=3.6,
                fiber=0,
                sugar=0,
                sodium=74
            ),
            'standard_portions': {'serving_size': 150, 'unit': 'grams'},
            'variations': ['marinated', 'plain'],
            'tags': ['chicken', 'protein', 'lean'],
            'is_composite': False,
            'embeddings': None
        }
    ],
    'Dinner': [
        {
            'id': 'DN001',
            'name': 'Baked Salmon',
            'local_name': 'Salmon Panggang',
            'category': FoodCategory.PROTEIN,
            'subcategory': 'Fish',
            'nutrition_per_100g': NutritionInfo(
                calories=206,
                protein=22.0,
                carbohydrates=0,
                fat=12.4,
                fiber=0,
                sugar=0,
                sodium=59
            ),
            'standard_portions': {'serving_size': 120, 'unit': 'grams'},
            'variations': ['with lemon', 'with herbs'],
            'tags': ['salmon', 'fish', 'omega3'],
            'is_composite': False,
            'embeddings': None
        }
    ],
    'Snack': [
        {
            'id': 'SN001',
            'name': 'Greek Yogurt',
            'local_name': 'Yogurt Yunani',
            'category': FoodCategory.SNACK,
            'subcategory': 'Yogurt',
            'nutrition_per_100g': NutritionInfo(
                calories=97,
                protein=10.0,
                carbohydrates=3.6,
                fat=5.0,
                fiber=0,
                sugar=3.6,
                sodium=36
            ),
            'standard_portions': {'serving_size': 170, 'unit': 'grams'},
            'variations': ['plain', 'with honey'],
            'tags': ['yogurt', 'protein', 'dairy'],
            'is_composite': False,
            'embeddings': None
        }
    ]
}


# Additional test case with missing portion data
mock_meal_data_no_portions = {
    'Breakfast': [
        {
            'id': 'BF002',
            'name': 'White Rice',
            'local_name': 'Nasi Putih',
            'category': FoodCategory.RICE_DISHES,
            'subcategory': 'Rice',
            'nutrition_per_100g': NutritionInfo(
                calories=130,
                protein=2.7,
                carbohydrates=28.2,
                fat=0.3,
                fiber=0.4,
                sugar=0.1,
                sodium=1
            ),
            'standard_portions': None,  # No portion info - AI will assume
            'variations': ['steamed'],
            'tags': ['rice', 'staple', 'carbs'],
            'is_composite': False,
            'embeddings': None
        },
        {
            'id': 'BF003',
            'name': 'Fried Egg',
            'local_name': 'Telur Mata Sapi',
            'category': FoodCategory.PROTEIN,
            'subcategory': 'Eggs',
            'nutrition_per_100g': NutritionInfo(
                calories=196,
                protein=13.6,
                carbohydrates=0.8,
                fat=15.3,
                fiber=0,
                sugar=0.4,
                sodium=207
            ),
            'standard_portions': {'serving_size': None, 'unit': 'grams'},  # Null serving_size
            'variations': ['sunny side up'],
            'tags': ['eggs', 'fried', 'protein'],
            'is_composite': False,
            'embeddings': None
        }
    ],
    'Lunch': [
        {
            'id': 'LN002',
            'name': 'Vegetable Stir Fry',
            'local_name': 'Tumis Sayur',
            'category': FoodCategory.VEGETABLE,
            'subcategory': 'Mixed Vegetables',
            'nutrition_per_100g': NutritionInfo(
                calories=65,
                protein=2.5,
                carbohydrates=8.2,
                fat=2.8,
                fiber=3.1,
                sugar=3.5,
                sodium=245
            ),
            'standard_portions': None,
            'variations': ['with garlic', 'spicy'],
            'tags': ['vegetables', 'healthy', 'fiber'],
            'is_composite': True,
            'embeddings': None
        }
    ]
}
