import base64
import datetime as dt
from django.core.files.base import ContentFile
from rest_framework import serializers
import webcolors
from djoser.serializers import UserSerializer

from .models import Cat, Collection


class Hex2NameColor(serializers.Field):
    def to_representation(self, value):
        return value
    
    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CatSerializer(serializers.ModelSerializer):
    color = Hex2NameColor()
    age = serializers.SerializerMethodField()
    image = Base64ImageField(required=False, allow_null=True)
    owner_username = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Cat
        fields = ('id', 'name', 'color', 'birth_year', 'owner', 'owner_username', 'age', 'image')
        read_only_fields = ('owner',)

    def get_age(self, obj):
        return dt.datetime.now().year - obj.birth_year
    
    def validate_birth_year(self, value):
        current_year = dt.datetime.now().year
        if value > current_year:
            raise serializers.ValidationError('Год рождения не может быть в будущем')
        return value


class CollectionSerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')
    cats_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()  
    is_liked = serializers.SerializerMethodField()
    cats = CatSerializer(many=True, read_only=True)  

    class Meta:
        model = Collection
        fields = (
            'id', 'name', 'description', 'category', 'owner', 'owner_username',
            'cats', 'cats_count', 'views_count', 'likes_count', 'is_liked',
            'created_at', 'updated_at'
        )
        read_only_fields = ('owner', 'views_count')

    def get_cats_count(self, obj):
        return obj.cats.count()
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False
    
    def validate_category(self, value):
        allowed_categories = [choice[0] for choice in Collection.CATEGORY_CHOICES]
        if value not in allowed_categories:
            raise serializers.ValidationError(f'Недопустимая категория. Выберите из: {", ".join(allowed_categories)}')
        return value
class CustomUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('is_staff',)