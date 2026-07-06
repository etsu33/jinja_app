from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from temples.api.serializers.reflection import ShrineReflectionSerializer
from temples.models import Shrine, ShrineReflection


class ShrineReflectionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None, id=None, shrine_id=None, *args, **kwargs):
        shrine_id = pk or id or shrine_id or request.data.get("shrine_id") or request.data.get("shrine")
        if not shrine_id:
            return Response({"detail": "shrine_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            shrine = Shrine.objects.get(pk=shrine_id)
        except Shrine.DoesNotExist:
            return Response({"detail": "Shrine not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        data["shrine"] = shrine.id

        serializer = ShrineReflectionSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        reflection = ShrineReflection.objects.create(
            user=request.user,
            shrine=shrine,
            history_theme=serializer.validated_data.get("history_theme") or "",
            prompt=serializer.validated_data.get("prompt") or "",
            answer=serializer.validated_data["answer"],
            mood_before=serializer.validated_data.get("mood_before") or "",
            mood_after=serializer.validated_data.get("mood_after") or "",
        )

        return Response(
            ShrineReflectionSerializer(reflection).data,
            status=status.HTTP_201_CREATED,
        )


class ShrineReflectionListView(generics.ListAPIView):
    serializer_class = ShrineReflectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            ShrineReflection.objects.filter(user=self.request.user)
            .select_related("shrine")
            .order_by("-created_at")
        )
