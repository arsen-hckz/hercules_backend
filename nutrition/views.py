import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import FoodItem, Recipe, SavedRecipe, MealLog
from .serializers import FoodItemSerializer, RecipeSerializer, MealLogSerializer


# ─── Food Items ──────────────────────────────────────────────────────────────

@api_view(['GET'])
def barcode_lookup(request, barcode):
    """
    Lookup a food item by barcode.
    1. Check local DB first.
    2. If not found, fetch from Open Food Facts by barcode and cache locally.
    """
    food = FoodItem.objects.filter(barcode=barcode).first()
    if food:
        return Response(FoodItemSerializer(food).data)

    cached = cache.get(f'off_barcode_{barcode}')
    if cached:
        return Response(cached)

    try:
        url = f'{settings.OPEN_FOOD_FACTS_URL}/product/{barcode}'
        resp = requests.get(url, params={'fields': 'id,product_name,brands,code,nutriments'}, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        product = data.get('product')
        if not product or not product.get('product_name'):
            return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        n = product.get('nutriments', {})
        food, _ = FoodItem.objects.get_or_create(
            off_id=product.get('id') or barcode,
            defaults={
                'name': product.get('product_name', 'Unknown'),
                'brand': product.get('brands', ''),
                'barcode': barcode,
                'calories': n.get('energy-kcal_100g', 0) or 0,
                'protein': n.get('proteins_100g', 0) or 0,
                'carbs': n.get('carbohydrates_100g', 0) or 0,
                'fat': n.get('fat_100g', 0) or 0,
                'fiber': n.get('fiber_100g', 0) or 0,
                'sugars': n.get('sugars_100g', 0) or 0,
            }
        )
        result = FoodItemSerializer(food).data
        cache.set(f'off_barcode_{barcode}', result, timeout=60 * 60 * 24 * 7)
        return Response(result)
    except Exception:
        return Response({'detail': 'Could not reach Open Food Facts.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class SubmitFoodView(generics.CreateAPIView):
    serializer_class = FoodItemSerializer

    def perform_create(self, serializer):
        import uuid
        serializer.save(
            submitted_by=self.request.user,
            is_verified=False,
            off_id=f'user-{self.request.user.id}-{uuid.uuid4().hex[:8]}',
        )


class FoodItemSearchView(generics.ListAPIView):
    serializer_class = FoodItemSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'brand']

    def get_queryset(self):
        return FoodItem.objects.all()

    def list(self, request, *args, **kwargs):
        query = request.query_params.get('search', '').strip()
        if not query:
            # Return all locally cached items so the user can browse
            qs = FoodItem.objects.all()[:50]
            return Response(FoodItemSerializer(qs, many=True).data)

        local_qs = FoodItem.objects.filter(name__icontains=query)[:20]
        if local_qs.exists():
            return Response(FoodItemSerializer(local_qs, many=True).data)

        cached = cache.get(f'off_search_{query}')
        if cached:
            return Response(cached)

        results = _fetch_from_off(query)
        cache.set(f'off_search_{query}', results, timeout=60 * 60 * 24)
        return Response(results)


def _fetch_from_off(query):
    """
    Search Open Food Facts with Greek-first priority:
    1. Greece only
    2. EU fallback
    3. Global fallback
    Skips products with missing/zero calorie data.
    """
    base_url = f'{settings.OPEN_FOOD_FACTS_URL}/search'
    fields = 'id,product_name,brands,code,nutriments,countries_tags'
    base_params = {
        'q': query,
        'page_size': 20,
        'fields': fields,
    }

    attempts = [
        {**base_params, 'countries_tags': 'en:greece'},
        {**base_params, 'countries_tags': 'en:european-union'},
        base_params,
    ]

    products = []
    for params in attempts:
        try:
            resp = requests.get(base_url, params=params, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            candidates = [
                p for p in data.get('products', [])
                if p.get('product_name')
                and p.get('nutriments', {}).get('energy-kcal_100g')
            ]
            if candidates:
                products = candidates
                break
        except Exception:
            continue

    items = []
    seen = set()
    for product in products:
        off_id = product.get('id') or product.get('code', '')
        if not off_id or off_id in seen:
            continue
        seen.add(off_id)

        n = product.get('nutriments', {})
        food, _ = FoodItem.objects.get_or_create(
            off_id=off_id,
            defaults={
                'name': product.get('product_name', 'Unknown'),
                'brand': product.get('brands', ''),
                'barcode': product.get('code', ''),
                'calories': n.get('energy-kcal_100g', 0) or 0,
                'protein': n.get('proteins_100g', 0) or 0,
                'carbs': n.get('carbohydrates_100g', 0) or 0,
                'fat': n.get('fat_100g', 0) or 0,
                'fiber': n.get('fiber_100g', 0) or 0,
                'sugars': n.get('sugars_100g', 0) or 0,
            }
        )
        items.append(FoodItemSerializer(food).data)
    return items


# ─── Recipes ─────────────────────────────────────────────────────────────────

class RecipeListCreateView(generics.ListCreateAPIView):
    serializer_class = RecipeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'user__username']
    ordering_fields = ['created_at']

    def get_queryset(self):
        return Recipe.objects.filter(is_public=True).select_related('user').prefetch_related('ingredients__food_item')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MyRecipesView(generics.ListAPIView):
    serializer_class = RecipeSerializer

    def get_queryset(self):
        return Recipe.objects.filter(user=self.request.user).prefetch_related('ingredients__food_item')


class RecipeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RecipeSerializer

    def get_queryset(self):
        return Recipe.objects.select_related('user').prefetch_related('ingredients__food_item')

    def perform_update(self, serializer):
        if self.get_object().user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied
        instance.delete()


@api_view(['POST'])
def save_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, is_public=True)
    _, created = SavedRecipe.objects.get_or_create(user=request.user, recipe=recipe)
    if not created:
        return Response({'detail': 'Already saved.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': 'Recipe saved.'}, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
def unsave_recipe(request, pk):
    deleted, _ = SavedRecipe.objects.filter(user=request.user, recipe_id=pk).delete()
    if not deleted:
        return Response({'detail': 'Not saved.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': 'Recipe unsaved.'})


class SavedRecipesView(generics.ListAPIView):
    serializer_class = RecipeSerializer

    def get_queryset(self):
        return Recipe.objects.filter(
            savedrecipe__user=self.request.user
        ).prefetch_related('ingredients__food_item')


# ─── Meal Logs ────────────────────────────────────────────────────────────────

class MealLogListCreateView(generics.ListCreateAPIView):
    serializer_class = MealLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['date', 'meal_type']

    def get_queryset(self):
        return MealLog.objects.filter(user=self.request.user).prefetch_related('items__food_item', 'items__recipe')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MealLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MealLogSerializer

    def get_queryset(self):
        return MealLog.objects.filter(user=self.request.user)


@api_view(['GET'])
def daily_nutrition_summary(request):
    from datetime import date as date_type
    date_param = request.query_params.get('date', date_type.today().isoformat())

    logs = MealLog.objects.filter(
        user=request.user, date=date_param
    ).prefetch_related('items__food_item', 'items__recipe')

    totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'fiber': 0, 'sugars': 0}
    for log in logs:
        n = log.total_nutrition()
        for key in totals:
            totals[key] += n[key]

    return Response({
        'date': date_param,
        'nutrition': {k: round(v, 1) for k, v in totals.items()},
        'tdee': request.user.calculate_tdee(),
        'goal': request.user.goal,
    })
