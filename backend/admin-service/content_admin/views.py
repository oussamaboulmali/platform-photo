from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Bloc, BlocItem, AdSlot
from .serializers import BlocSerializer, BlocItemSerializer, AdSlotSerializer


class BlocViewSet(viewsets.ModelViewSet):
    queryset = Bloc.objects.all()
    serializer_class = BlocSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = self.queryset
        user_role = self.request.META.get('HTTP_X_USER_ROLE', '')
        
        # Public users only see visible blocs
        if user_role not in ['admin', 'validator']:
            queryset = queryset.filter(visible=True)
            now = timezone.now()
            queryset = queryset.filter(
                models.Q(start_at__isnull=True) | models.Q(start_at__lte=now),
                models.Q(end_at__isnull=True) | models.Q(end_at__gte=now)
            )
        
        return queryset.order_by('order')

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        bloc = self.get_object()
        image_id = request.data.get('image_id')
        
        if not image_id:
            return Response({'error': 'image_id required'}, status=400)
        
        item = BlocItem.objects.create(
            bloc=bloc,
            image_id=image_id,
            order=request.data.get('order', 0),
            title_override=request.data.get('title_override', ''),
            description_override=request.data.get('description_override', '')
        )
        
        return Response(BlocItemSerializer(item).data, status=201)


class AdSlotViewSet(viewsets.ModelViewSet):
    queryset = AdSlot.objects.all()
    serializer_class = AdSlotSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = self.queryset
        user_role = self.request.META.get('HTTP_X_USER_ROLE', '')
        
        # Public users only see active ads
        if user_role not in ['admin']:
            queryset = queryset.filter(active=True)
            now = timezone.now()
            queryset = queryset.filter(
                models.Q(start_at__isnull=True) | models.Q(start_at__lte=now),
                models.Q(end_at__isnull=True) | models.Q(end_at__gte=now)
            )
        
        # Filter by position
        position = self.request.query_params.get('position')
        if position:
            queryset = queryset.filter(position=position)
        
        return queryset.order_by('priority')

    @action(detail=True, methods=['post'])
    def track_impression(self, request, pk=None):
        ad = self.get_object()
        ad.increment_impressions()
        return Response({'current_impressions': ad.current_impressions})
