"""Saved-payee REST endpoints."""

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsActiveAccount
from apps.payments import payee_services, selectors
from apps.payments.serializers import (
    PayeeCreateSerializer,
    PayeeSerializer,
    PayeeUpdateSerializer,
)


def _success(data, message=""):
    return {"success": True, "data": data, "message": message}


class PayeeListCreateView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request):
        search = request.query_params.get("search", "").strip()
        favorite_param = request.query_params.get("favorite")
        if favorite_param is None:
            favorite = None
        elif favorite_param.lower() in ("true", "1"):
            favorite = True
        elif favorite_param.lower() in ("false", "0"):
            favorite = False
        else:
            raise ValidationError({"favorite": "Use true or false."})
        payees = selectors.list_payees(request.user, search=search[:120], favorite=favorite)
        return Response(_success(PayeeSerializer(payees, many=True).data))

    def post(self, request):
        serializer = PayeeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payee = payee_services.create_payee(request.user, serializer.validated_data)
        return Response(
            _success(PayeeSerializer(payee).data, "Saved payee created."),
            status=status.HTTP_201_CREATED,
        )


class PayeeDetailView(APIView):
    permission_classes = [IsActiveAccount]

    def get(self, request, public_id):
        payee = payee_services.require_payee(request.user, public_id)
        return Response(_success(PayeeSerializer(payee).data))

    def patch(self, request, public_id):
        payee = payee_services.require_payee(request.user, public_id)
        serializer = PayeeUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        payee = payee_services.update_payee(request.user, payee, serializer.validated_data)
        return Response(_success(PayeeSerializer(payee).data, "Saved payee updated."))

    def delete(self, request, public_id):
        payee = payee_services.require_payee(request.user, public_id)
        payee_services.delete_payee(request.user, payee)
        return Response(_success({}, "Saved payee deleted."))
