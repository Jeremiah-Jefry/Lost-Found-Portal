from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Item, ItemLog, Match
from .permissions import IsStaffOrAdmin, IsAdminRole, IsOwnerOrStaff
from .serializers import (
    ItemSerializer, ItemListSerializer,
    ItemLogSerializer, MatchSerializer,
)
from users.models import User
from users.serializers import UserBriefSerializer


# ── Auto-match engine ──────────────────────────────────────────────────────────

def run_auto_match(item: Item) -> None:
    """
    Score-based matcher:  category match = +3 pts,  location match = +2 pts.
    Minimum threshold = 2.  Creates or updates Match rows; writes MATCH_FOUND log.
    """
    if item.resolution_status == 'RETURNED':
        return

    if item.status == 'FOUND':
        candidates = Item.objects.filter(
            status='LOST',
            resolution_status__in=['OPEN', 'SECURED'],
        ).exclude(id=item.id)
    else:
        candidates = Item.objects.filter(
            status='FOUND',
            resolution_status__in=['OPEN', 'SECURED'],
        ).exclude(id=item.id)

    for candidate in candidates:
        score = 0
        if item.category == candidate.category:
            score += 3
        if item.location.strip().lower() == candidate.location.strip().lower():
            score += 2

        if score < 2:
            continue

        found_item = item      if item.status == 'FOUND' else candidate
        lost_item  = candidate if item.status == 'FOUND' else item

        match, created = Match.objects.update_or_create(
            found_item=found_item,
            lost_item=lost_item,
            defaults={'score': score},
        )
        if created:
            # Log on both items
            for target in (found_item, lost_item):
                ItemLog.objects.create(
                    item=target,
                    actor=None,
                    actor_role='SYSTEM',
                    action='MATCH_FOUND',
                    note=f'Potential match found (score={score})',
                )


# ── Item pagination ────────────────────────────────────────────────────────────

class ItemPagination(PageNumberPagination):
    page_size      = 20
    max_page_size  = 100
    page_size_query_param = 'page_size'


# ── Item List / Create ─────────────────────────────────────────────────────────

class ItemListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/items/  — public feed (read); query params: q, status, category
    POST /api/items/  — authenticated users only
    """
    pagination_class = ItemPagination
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ['title', 'description', 'location']
    ordering_fields  = ['date_reported', 'title']
    ordering         = ['-date_reported']

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ItemListSerializer
        return ItemSerializer

    def get_queryset(self):
        qs = Item.objects.select_related('reporter').all()

        status_filter   = self.request.query_params.get('status')
        category_filter = self.request.query_params.get('category')
        q               = self.request.query_params.get('q', '').strip()
        resolution      = self.request.query_params.get('resolution')

        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        if category_filter:
            qs = qs.filter(category=category_filter.upper())
        if resolution:
            qs = qs.filter(resolution_status=resolution.upper())
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(location__icontains=q)
            )
        return qs

    def perform_create(self, serializer):
        item = serializer.save(reporter=self.request.user)
        ItemLog.objects.create(
            item=item,
            actor=self.request.user,
            actor_role=self.request.user.role,
            action='CREATED',
            note=f'Reported as {item.status}',
        )
        run_auto_match(item)


# ── Item Retrieve / Update / Delete ───────────────────────────────────────────

class ItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/items/<id>/  — public
    PUT    /api/items/<id>/  — owner or STAFF/ADMIN
    PATCH  /api/items/<id>/  — owner or STAFF/ADMIN
    DELETE /api/items/<id>/  — owner or ADMIN
    """
    serializer_class = ItemSerializer
    queryset         = Item.objects.select_related('reporter').prefetch_related('logs__actor')

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        if self.request.method == 'DELETE':
            return [IsAuthenticated(), IsOwnerOrStaff()]
        return [IsAuthenticated(), IsOwnerOrStaff()]

    def perform_update(self, serializer):
        old = self.get_object()
        item = serializer.save()
        ItemLog.objects.create(
            item=item,
            actor=self.request.user,
            actor_role=self.request.user.role,
            action='EDITED',
            note='Item details updated',
        )
        run_auto_match(item)


# ── Resolve (close) an item ────────────────────────────────────────────────────

class ResolveItemView(APIView):
    """
    POST /api/items/<id>/resolve/

    RBAC resolve rules (exact Flask parity):
      ADMIN          — can always resolve
      STAFF          — can resolve any item (including SECURITY-held)
      USER (owner)   — can only resolve their own item IF handover != SECURITY
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            item = Item.objects.get(pk=pk)
        except Item.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        if item.resolution_status == 'RETURNED':
            return Response({'detail': 'Item is already resolved.'}, status=status.HTTP_400_BAD_REQUEST)

        # RBAC gate
        if user.role == 'ADMIN':
            pass  # ADMIN bypasses all gates
        elif user.role == 'STAFF':
            pass  # STAFF can close any item
        elif item.reporter == user:
            if item.handover_status == 'SECURITY':
                return Response(
                    {'detail': 'This item is held by Security. Only staff can mark it returned.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        receiver_name    = request.data.get('receiver_name', '').strip()[:100] or None
        receiver_contact = request.data.get('receiver_contact', '').strip()[:100] or None

        old_status = item.resolution_status
        item.resolution_status = 'RETURNED'
        if receiver_name:
            item.receiver_name = receiver_name
        if receiver_contact:
            item.receiver_contact = receiver_contact
        item.save(update_fields=['resolution_status', 'receiver_name', 'receiver_contact'])

        ItemLog.objects.create(
            item=item,
            actor=user,
            actor_role=user.role,
            action='RESOLVED',
            note='Item marked as returned to owner',
            from_value=old_status,
            to_value='RETURNED',
        )

        return Response(ItemSerializer(item, context={'request': request}).data)


# ── Update handover ────────────────────────────────────────────────────────────

class HandoverUpdateView(APIView):
    """PATCH /api/items/<id>/handover/ — STAFF/ADMIN only."""
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

    ALLOWED_HANDOVERS = {'LEFT_AT_LOCATION', 'WITH_FINDER', 'SECURITY', ''}

    def patch(self, request, pk):
        try:
            item = Item.objects.get(pk=pk)
        except Item.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        hs = request.data.get('handover_status', '').strip()
        if hs not in self.ALLOWED_HANDOVERS:
            return Response({'detail': 'Invalid handover_status.'}, status=status.HTTP_400_BAD_REQUEST)

        old_hs = item.handover_status or ''
        item.handover_status  = hs or None
        item.handover_details = request.data.get('handover_details', item.handover_details)
        if item.resolution_status == 'OPEN' and hs == 'SECURITY':
            item.resolution_status = 'SECURED'
        item.save(update_fields=['handover_status', 'handover_details', 'resolution_status'])

        ItemLog.objects.create(
            item=item,
            actor=request.user,
            actor_role=request.user.role,
            action='HANDOVER_UPDATED',
            from_value=old_hs or None,
            to_value=hs or None,
        )

        return Response(ItemSerializer(item, context={'request': request}).data)


# ── Status change (OPEN → SECURED) ────────────────────────────────────────────

class StatusChangeView(APIView):
    """PATCH /api/items/<id>/status/ — STAFF/ADMIN only."""
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

    ALLOWED = {'OPEN', 'SECURED', 'RETURNED'}

    def patch(self, request, pk):
        try:
            item = Item.objects.get(pk=pk)
        except Item.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('resolution_status', '').strip().upper()
        if new_status not in self.ALLOWED:
            return Response({'detail': 'Invalid resolution_status.'}, status=status.HTTP_400_BAD_REQUEST)

        old_status = item.resolution_status
        item.resolution_status = new_status
        item.save(update_fields=['resolution_status'])

        ItemLog.objects.create(
            item=item,
            actor=request.user,
            actor_role=request.user.role,
            action='STATUS_CHANGED',
            from_value=old_status,
            to_value=new_status,
        )

        return Response(ItemSerializer(item, context={'request': request}).data)


# ── My items ───────────────────────────────────────────────────────────────────

class MyItemsView(generics.ListAPIView):
    """GET /api/items/mine/ — returns items reported by the current user."""
    serializer_class = ItemListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ItemPagination

    def get_queryset(self):
        return Item.objects.filter(reporter=self.request.user).select_related('reporter')


# ── Matches ────────────────────────────────────────────────────────────────────

class MatchListView(generics.ListAPIView):
    """GET /api/matches/ — STAFF/ADMIN only: all unreviewed matches."""
    serializer_class   = MatchSerializer
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

    def get_queryset(self):
        return Match.objects.select_related(
            'found_item__reporter', 'lost_item__reporter'
        ).filter(is_reviewed=False)


class MatchReviewView(APIView):
    """POST /api/matches/<id>/review/ — mark a match as reviewed."""
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

    def post(self, request, pk):
        try:
            match = Match.objects.get(pk=pk)
        except Match.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        match.is_reviewed = True
        match.save(update_fields=['is_reviewed'])
        return Response(MatchSerializer(match, context={'request': request}).data)


# ── Admin Analytics ────────────────────────────────────────────────────────────

class AdminAnalyticsView(APIView):
    """GET /api/analytics/ — ADMIN only."""
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        from django.db.models.functions import TruncDate

        now = timezone.now()

        # Overview counts
        total_items    = Item.objects.count()
        total_lost     = Item.objects.filter(status='LOST',  resolution_status__in=['OPEN','SECURED']).count()
        total_found    = Item.objects.filter(status='FOUND', resolution_status__in=['OPEN','SECURED']).count()
        total_returned = Item.objects.filter(resolution_status='RETURNED').count()
        total_open     = Item.objects.filter(resolution_status='OPEN').count()
        total_secured  = Item.objects.filter(resolution_status='SECURED').count()

        # Same-day retrieval rate
        returned_items = Item.objects.filter(resolution_status='RETURNED')
        total_resolved = returned_items.count()
        same_day_count = 0
        for item in returned_items:
            logs = item.logs.filter(action='RESOLVED').order_by('created_at').first()
            if logs and logs.created_at.date() == item.date_reported.date():
                same_day_count += 1
        same_day_rate = round((same_day_count / total_resolved * 100) if total_resolved else 0, 1)

        # Handover stats
        handover_security    = Item.objects.filter(handover_status='SECURITY').count()
        handover_with_finder = Item.objects.filter(handover_status='WITH_FINDER').count()
        handover_left        = Item.objects.filter(handover_status='LEFT_AT_LOCATION').count()

        # User roster
        total_users = User.objects.filter(role='USER').count()
        total_staff = User.objects.filter(role__in=['STAFF', 'ADMIN']).count()
        staff_users = User.objects.filter(role__in=['STAFF', 'ADMIN']).order_by('role', 'username')

        # Daily activity — last 7 days
        daily_activity = []
        for i in range(6, -1, -1):
            day = now.date() - timedelta(days=i)
            lost_count  = Item.objects.filter(status='LOST',  date_reported__date=day).count()
            found_count = Item.objects.filter(status='FOUND', date_reported__date=day).count()
            daily_activity.append({
                'date':  day.strftime('%a'),
                'lost':  lost_count,
                'found': found_count,
            })

        # Recent audit logs
        recent_logs = ItemLog.objects.select_related('actor', 'item').order_by('-created_at')[:25]

        return Response({
            'overview': {
                'total_items':    total_items,
                'total_lost':     total_lost,
                'total_found':    total_found,
                'total_returned': total_returned,
                'total_open':     total_open,
                'total_secured':  total_secured,
            },
            'metrics': {
                'same_day_rate':  same_day_rate,
                'same_day_count': same_day_count,
                'total_resolved': total_resolved,
            },
            'handover': {
                'security':    handover_security,
                'with_finder': handover_with_finder,
                'left':        handover_left,
            },
            'users': {
                'total_users':  total_users,
                'total_staff':  total_staff,
                'staff_roster': UserBriefSerializer(staff_users, many=True).data,
            },
            'daily_activity': daily_activity,
            'recent_logs': ItemLogSerializer(recent_logs, many=True).data,
        })


# ── Dashboard snapshot (STAFF/ADMIN) ──────────────────────────────────────────

class DashboardView(APIView):
    """GET /api/dashboard/ — STAFF/ADMIN: live counts + recent items."""
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

    def get(self, request):
        now = timezone.now()
        today = now.date()

        open_lost  = Item.objects.filter(status='LOST',  resolution_status='OPEN').order_by('-date_reported')[:10]
        open_found = Item.objects.filter(status='FOUND', resolution_status__in=['OPEN','SECURED']).order_by('-date_reported')[:10]
        unreviewed_matches = Match.objects.filter(is_reviewed=False).count()

        new_today = Item.objects.filter(date_reported__date=today).count()

        return Response({
            'counts': {
                'open_lost':          Item.objects.filter(status='LOST',  resolution_status='OPEN').count(),
                'open_found':         Item.objects.filter(status='FOUND', resolution_status__in=['OPEN','SECURED']).count(),
                'secured':            Item.objects.filter(resolution_status='SECURED').count(),
                'returned':           Item.objects.filter(resolution_status='RETURNED').count(),
                'unreviewed_matches': unreviewed_matches,
                'new_today':          new_today,
            },
            'recent_lost':  ItemListSerializer(open_lost,  many=True, context={'request': request}).data,
            'recent_found': ItemListSerializer(open_found, many=True, context={'request': request}).data,
        })
