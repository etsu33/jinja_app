from __future__ import annotations

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status

from temples.api.serializers.shrine_submission import ShrineSubmissionCreateSerializer
from temples.services.shrine_submission import (
    find_duplicate_candidates,
    normalize_shrine_address,
    normalize_shrine_name,
    serialize_duplicate_candidates,
)


class ShrineSubmissionCreateView(generics.CreateAPIView):
    serializer_class = ShrineSubmissionCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        normalized_name = normalize_shrine_name(serializer.validated_data.get("name", ""))
        normalized_address = normalize_shrine_address(serializer.validated_data.get("address", ""))
        duplicate_candidates = find_duplicate_candidates(
            name=normalized_name,
            address=normalized_address,
        )
        if duplicate_candidates:
            return Response(
                {
                    "code": "duplicate_candidate",
                    "message": "この神社はすでに登録されている可能性があります。",
                    "candidates": serialize_duplicate_candidates(duplicate_candidates),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        submission = serializer.save()

        response_serializer = self.get_serializer(submission)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
