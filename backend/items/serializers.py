from rest_framework import serializers
from django.conf import settings
from .models import Item, ItemLog, Match
from users.serializers import UserBriefSerializer


class ItemLogSerializer(serializers.ModelSerializer):
    actor        = UserBriefSerializer(read_only=True)
    action_label = serializers.ReadOnlyField()
    action_icon  = serializers.ReadOnlyField()

    class Meta:
        model  = ItemLog
        fields = [
            'id', 'actor', 'actor_role', 'action', 'action_label',
            'action_icon', 'note', 'from_value', 'to_value', 'created_at',
        ]


class ItemSerializer(serializers.ModelSerializer):
    reporter       = UserBriefSerializer(read_only=True)
    image_url      = serializers.SerializerMethodField()
    status_label   = serializers.ReadOnlyField()
    category_label = serializers.ReadOnlyField()
    handover_label = serializers.ReadOnlyField()
    resolution_label = serializers.ReadOnlyField()
    logs           = ItemLogSerializer(many=True, read_only=True)

    class Meta:
        model  = Item
        fields = [
            'id', 'title', 'description', 'status', 'status_label',
            'category', 'category_label', 'location', 'image', 'image_url',
            'resolution_status', 'resolution_label',
            'handover_status', 'handover_label', 'handover_details',
            'receiver_name', 'receiver_contact',
            'date_reported', 'created_at',
            'reporter', 'logs',
        ]
        read_only_fields = ['id', 'date_reported', 'created_at', 'reporter']
        extra_kwargs = {'image': {'required': False, 'allow_null': True}}

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url


class ItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list endpoints — no logs."""
    reporter       = UserBriefSerializer(read_only=True)
    image_url      = serializers.SerializerMethodField()
    status_label   = serializers.ReadOnlyField()
    category_label = serializers.ReadOnlyField()
    resolution_label = serializers.ReadOnlyField()
    handover_label = serializers.ReadOnlyField()

    class Meta:
        model  = Item
        fields = [
            'id', 'title', 'status', 'status_label', 'category', 'category_label',
            'location', 'image_url', 'resolution_status', 'resolution_label',
            'handover_status', 'handover_label', 'date_reported', 'reporter',
        ]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url


class MatchSerializer(serializers.ModelSerializer):
    found_item = ItemListSerializer(read_only=True)
    lost_item  = ItemListSerializer(read_only=True)

    class Meta:
        model  = Match
        fields = ['id', 'found_item', 'lost_item', 'score', 'is_reviewed', 'created_at']
