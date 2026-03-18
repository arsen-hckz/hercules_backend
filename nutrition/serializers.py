from rest_framework import serializers
from .models import FoodItem, Recipe, RecipeIngredient, SavedRecipe, MealLog, MealLogItem


class FoodItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodItem
        fields = [
            'id', 'name', 'brand', 'barcode',
            'calories', 'protein', 'carbs', 'fat', 'fiber', 'sugars',
        ]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    food_item = FoodItemSerializer(read_only=True)
    food_item_id = serializers.PrimaryKeyRelatedField(
        queryset=FoodItem.objects.all(), source='food_item', write_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'food_item', 'food_item_id', 'quantity_grams']


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True)
    nutrition_per_serving = serializers.SerializerMethodField()
    author = serializers.StringRelatedField(source='user', read_only=True)
    is_saved = serializers.SerializerMethodField()
    saves_count = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'author', 'title', 'description', 'instructions',
            'servings', 'is_public', 'image',
            'ingredients', 'nutrition_per_serving',
            'is_saved', 'saves_count', 'created_at',
        ]
        read_only_fields = ['author']

    def get_nutrition_per_serving(self, obj):
        return obj.nutrition_per_serving()

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedRecipe.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def get_saves_count(self, obj):
        return obj.saved_by.count()

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        for ing in ingredients_data:
            RecipeIngredient.objects.create(recipe=recipe, **ing)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if ingredients_data is not None:
            instance.ingredients.all().delete()
            for ing in ingredients_data:
                RecipeIngredient.objects.create(recipe=instance, **ing)
        return instance


class MealLogItemSerializer(serializers.ModelSerializer):
    food_item = FoodItemSerializer(read_only=True)
    food_item_id = serializers.PrimaryKeyRelatedField(
        queryset=FoodItem.objects.all(), source='food_item', write_only=True, required=False
    )
    recipe_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('nutrition.models', fromlist=['Recipe']).Recipe.objects.all(),
        source='recipe', write_only=True, required=False
    )
    nutrition = serializers.SerializerMethodField()

    class Meta:
        model = MealLogItem
        fields = [
            'id', 'food_item', 'food_item_id', 'recipe_id',
            'quantity_grams', 'servings', 'nutrition',
        ]

    def get_nutrition(self, obj):
        return obj.get_nutrition()


class MealLogSerializer(serializers.ModelSerializer):
    items = MealLogItemSerializer(many=True)
    total_nutrition = serializers.SerializerMethodField()

    class Meta:
        model = MealLog
        fields = ['id', 'date', 'meal_type', 'notes', 'items', 'total_nutrition', 'created_at']

    def get_total_nutrition(self, obj):
        return obj.total_nutrition()

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        meal_log = MealLog.objects.create(**validated_data)
        for item in items_data:
            MealLogItem.objects.create(meal_log=meal_log, **item)
        return meal_log
