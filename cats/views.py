from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from django.db import models

from .models import Cat, Collection
from .serializers import CatSerializer, CollectionSerializer
from .permissions import IsOwnerOrAdminOrReadOnly


class CatViewSet(viewsets.ModelViewSet):
    queryset = Cat.objects.all()
    serializer_class = CatSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdminOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class CollectionPagination(PageNumberPagination):
    page_size = 9


class CatPagination(PageNumberPagination):
    page_size = 9
    page_size_query_param = 'page_size'
    max_page_size = 50


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdminOrReadOnly]
    pagination_class = CollectionPagination

    def get_queryset(self):
        queryset = Collection.objects.all()
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        sort_by = self.request.query_params.get('sort')
        if sort_by == 'popular':
            queryset = queryset.annotate(
                likes_count=models.Count('likes')
            ).order_by('-likes_count', '-created_at')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrAdminOrReadOnly])
    def add_cat(self, request, pk=None):
        collection = self.get_object()
        cat_id = request.data.get('cat_id')
        
        if not cat_id:
            return Response({"detail": "Не указан ID котика"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cat = Cat.objects.get(id=cat_id)
        except Cat.DoesNotExist:
            return Response({"detail": "Котик не найден"}, status=status.HTTP_404_NOT_FOUND)
        
        if cat in collection.cats.all():
            return Response({"detail": "Котик уже в подборке"}, status=status.HTTP_400_BAD_REQUEST)
        
        collection.cats.add(cat)
        return Response({"detail": "Котик добавлен в подборку"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrAdminOrReadOnly])
    def remove_cat(self, request, pk=None):
        collection = self.get_object()
        cat_id = request.data.get('cat_id')
        
        if not cat_id:
            return Response({"detail": "Не указан ID котика"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cat = Cat.objects.get(id=cat_id)
        except Cat.DoesNotExist:
            return Response({"detail": "Котик не найден"}, status=status.HTTP_404_NOT_FOUND)
        
        if cat not in collection.cats.all():
            return Response({"detail": "Котик не найден в подборке"}, status=status.HTTP_404_NOT_FOUND)
        
        collection.cats.remove(cat)
        return Response({"detail": "Котик удалён из подборки"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        collection = self.get_object()
        user = request.user
    
        if user in collection.likes.all():
            return Response({"detail": "Вы уже поставили лайк"}, status=status.HTTP_400_BAD_REQUEST)
    
        collection.likes.add(user)
        return Response({
            "detail": "Лайк поставлен",
            "likes_count": collection.likes.count()
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        collection = self.get_object()
        user = request.user
    
        if user not in collection.likes.all():
            return Response({"detail": "Вы не лайкали эту подборку"}, status=status.HTTP_400_BAD_REQUEST)
    
        collection.likes.remove(user)
        return Response({
            "detail": "Лайк убран",
            "likes_count": collection.likes.count()
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        popular_collections = Collection.objects.annotate(
            likes_count=models.Count('likes')
        ).filter(likes_count__gt=0).order_by('-likes_count', '-created_at')[:5]
        
        serializer = self.get_serializer(popular_collections, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def cats_paginated(self, request, pk=None):
        collection = self.get_object()
        cats = collection.cats.all()
    
        paginator = CatPagination()
        page = paginator.paginate_queryset(cats, request)
        if page is not None:
            serializer = CatSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        
        serializer = CatSerializer(cats, many=True, context={'request': request})
        return Response(serializer.data)
