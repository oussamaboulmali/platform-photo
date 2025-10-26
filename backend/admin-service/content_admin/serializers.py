from rest_framework import serializers
from .models import Bloc, BlocItem, AdSlot


class BlocItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlocItem
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class BlocSerializer(serializers.ModelSerializer):
    items = BlocItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Bloc
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AdSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdSlot
        fields = '__all__'
        read_only_fields = ['id', 'current_impressions', 'created_at', 'updated_at']
