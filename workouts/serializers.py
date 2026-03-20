from rest_framework import serializers
from .models import MuscleGroup, Exercise, ExerciseMuscleActivation, WorkoutSession, WorkoutEntry, WorkoutSet


class MuscleGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = MuscleGroup
        fields = ['id', 'name']


class ExerciseMuscleActivationSerializer(serializers.ModelSerializer):
    muscle_group = MuscleGroupSerializer(read_only=True)
    muscle_group_id = serializers.PrimaryKeyRelatedField(
        queryset=MuscleGroup.objects.all(), source='muscle_group', write_only=True
    )

    class Meta:
        model = ExerciseMuscleActivation
        fields = ['id', 'muscle_group', 'muscle_group_id', 'level']


class ExerciseSerializer(serializers.ModelSerializer):
    muscle_activations = ExerciseMuscleActivationSerializer(many=True, read_only=True)

    class Meta:
        model = Exercise
        fields = [
            'id', 'name', 'equipment', 'description', 'is_custom', 'muscle_activations',
        ]
        read_only_fields = ['is_custom']


class WorkoutSetSerializer(serializers.ModelSerializer):
    volume = serializers.ReadOnlyField()

    class Meta:
        model = WorkoutSet
        fields = ['id', 'set_number', 'weight_kg', 'reps', 'rest_seconds', 'is_warmup', 'volume']


class WorkoutEntrySerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)
    exercise_id = serializers.PrimaryKeyRelatedField(
        queryset=Exercise.objects.all(), source='exercise', write_only=True
    )
    sets = WorkoutSetSerializer(many=True)

    class Meta:
        model = WorkoutEntry
        fields = ['id', 'exercise', 'exercise_id', 'order', 'notes', 'sets']

    def create(self, validated_data):
        sets_data = validated_data.pop('sets')
        entry = WorkoutEntry.objects.create(**validated_data)
        for s in sets_data:
            WorkoutSet.objects.create(entry=entry, **s)
        return entry


class WorkoutSessionSerializer(serializers.ModelSerializer):
    entries = WorkoutEntrySerializer(many=True)
    total_volume = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutSession
        fields = [
            'id', 'name', 'date', 'notes', 'duration_minutes',
            'entries', 'total_volume', 'created_at',
        ]

    def get_total_volume(self, obj):
        return obj.total_volume()

    def create(self, validated_data):
        entries_data = validated_data.pop('entries')
        session = WorkoutSession.objects.create(**validated_data)
        for entry_data in entries_data:
            sets_data = entry_data.pop('sets')
            entry = WorkoutEntry.objects.create(session=session, **entry_data)
            for s in sets_data:
                WorkoutSet.objects.create(entry=entry, **s)
        return session


class WorkoutSessionListSerializer(serializers.ModelSerializer):
    total_volume = serializers.SerializerMethodField()
    exercises_count = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutSession
        fields = ['id', 'name', 'date', 'duration_minutes', 'total_volume', 'exercises_count']

    def get_total_volume(self, obj):
        return obj.total_volume()

    def get_exercises_count(self, obj):
        return obj.entries.count()
