from rest_framework import generics, status, filters, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Exercise, ExerciseMuscleActivation, MuscleGroup, WorkoutSession
from .serializers import (
    ExerciseSerializer, ExerciseMuscleActivationSerializer, MuscleGroupSerializer,
    WorkoutSessionSerializer, WorkoutSessionListSerializer
)


class MuscleGroupListView(generics.ListAPIView):
    serializer_class = MuscleGroupSerializer
    queryset = MuscleGroup.objects.all()
    pagination_class = None


class ExerciseListCreateView(generics.ListCreateAPIView):
    serializer_class = ExerciseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['equipment']
    search_fields = ['name']

    def get_queryset(self):
        return Exercise.objects.filter(
            is_custom=False
        ) | Exercise.objects.filter(
            is_custom=True, created_by=self.request.user
        )

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save(is_custom=False)
        else:
            serializer.save(is_custom=True, created_by=self.request.user)


class ExerciseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExerciseSerializer

    def get_queryset(self):
        return Exercise.objects.all()


class WorkoutSessionListCreateView(generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date']
    ordering_fields = ['date']
    ordering = ['-date']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WorkoutSessionSerializer
        return WorkoutSessionListSerializer

    def get_queryset(self):
        return WorkoutSession.objects.filter(user=self.request.user).prefetch_related(
            'entries__exercise', 'entries__sets'
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WorkoutSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WorkoutSessionSerializer

    def get_queryset(self):
        return WorkoutSession.objects.filter(user=self.request.user).prefetch_related(
            'entries__exercise', 'entries__sets'
        )


@api_view(['GET'])
def exercise_progress(request, exercise_id):
    """Return best set (max weight) per session for a given exercise."""
    sessions = WorkoutSession.objects.filter(
        user=request.user,
        entries__exercise_id=exercise_id
    ).order_by('date').distinct()

    progress = []
    for session in sessions:
        best = None
        for entry in session.entries.filter(exercise_id=exercise_id):
            for s in entry.sets.filter(is_warmup=False):
                if s.weight_kg and (best is None or s.weight_kg > best['weight_kg']):
                    best = {'weight_kg': s.weight_kg, 'reps': s.reps}
        if best:
            progress.append({
                'date': session.date,
                'best_set': best,
                'volume': session.total_volume(),
            })

    return Response(progress)


@api_view(['GET'])
def workout_stats(request):
    """Summary stats for the authenticated user."""
    sessions = WorkoutSession.objects.filter(user=request.user)
    return Response({
        'total_sessions': sessions.count(),
        'total_volume': sum(s.total_volume() for s in sessions),
    })


@api_view(['GET'])
def diet_workout_correlation(request):
    """
    For each day in the last N days (default 30), compare:
    - calories consumed vs TDEE target
    - whether the user trained that day
    Returns a daily breakdown + insight flags.
    """
    from datetime import date, timedelta
    from nutrition.models import MealLog

    days = int(request.query_params.get('days', 30))
    tdee = request.user.calculate_tdee()
    today = date.today()

    workout_dates = set(
        WorkoutSession.objects.filter(user=request.user)
        .values_list('date', flat=True)
    )

    result = []
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        logs = MealLog.objects.filter(
            user=request.user, date=day
        ).prefetch_related('items__food_item', 'items__recipe')

        calories = sum(
            log.total_nutrition()['calories'] for log in logs
        )
        trained = day in workout_dates

        insight = None
        if tdee:
            if trained and calories < tdee * 0.85:
                insight = 'under_fueled'
            elif not trained and calories > tdee * 1.15:
                insight = 'surplus_on_rest_day'
            elif trained and calories >= tdee * 0.95:
                insight = 'well_fueled'

        result.append({
            'date': day,
            'calories': round(calories, 1),
            'tdee_target': tdee,
            'trained': trained,
            'insight': insight,
        })

    return Response(result)


class ExerciseMuscleActivationCreateView(generics.CreateAPIView):
    """Add a muscle group activation to an exercise."""
    serializer_class = ExerciseMuscleActivationSerializer

    def perform_create(self, serializer):
        exercise = generics.get_object_or_404(Exercise, pk=self.kwargs['exercise_id'])
        serializer.save(exercise=exercise)


class ExerciseMuscleActivationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Edit (level) or delete a single muscle activation."""
    serializer_class = ExerciseMuscleActivationSerializer
    queryset = ExerciseMuscleActivation.objects.all()


class AdminExerciseListView(generics.ListAPIView):
    """Admin: all exercises, no pagination."""
    serializer_class = ExerciseSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name']
    filterset_fields = ['equipment']
    pagination_class = None
    queryset = Exercise.objects.prefetch_related('muscle_activations__muscle_group').order_by('name')


class AdminSessionListView(generics.ListAPIView):
    """Admin: view any user's workout sessions by passing ?user_id="""
    serializer_class = WorkoutSessionListSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date']
    ordering = ['-date']

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        qs = WorkoutSession.objects.prefetch_related('entries__exercise', 'entries__sets')
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs
