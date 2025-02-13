from user_app.models import User
from rest_framework import status
from user_app.utils import Util
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAdminUser
from user_app.serializer.admin_serializers import *
from rest_framework.generics import CreateAPIView, UpdateAPIView, ListAPIView

# API: AdminLogin
# -----------------------------------------------------------------------------------------
class AdminLoginAPIView(CreateAPIView):
    """
    Handles admin login and returns JWT tokens upon successful authentication.
    
    Attributes:
        serializer_class (Serializer): The serializer used for admin login validation.
    """
    serializer_class = AdminLoginSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Validates the admin login credentials and returns JWT tokens.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: A Response containing JWT tokens and HTTP 200 status.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        tokens = Util.get_tokens_for_user(user)
        return Response(tokens, status=status.HTTP_200_OK)
    
# API: AdminUpdatePrayPoints
# ----------------------------------------------------------------------------------------------
class AdminUpdatePrayPointsAPIView(UpdateAPIView):
    """
    Allows admin to update pray points for a user by providing either telegram_id or username.
    
    Attributes:
        permission_classes (list): List of permissions required for the view.
        serializer_class (Serializer): Serializer for updating user points.
    """
    permission_classes = [IsAdminUser]
    serializer_class = AdminUpdatePointsSerializer

    def get_object(self):
        """
        Retrieves the user instance based on telegram_id or username.

        Returns:
            User: The user instance.

        Raises:
            NotFound: If neither telegram_id nor username is provided or if the user is not found.
        """
        # Get the telegram_id from the request data
        telegram_id = self.request.data.get("telegram_id")
        username = self.request.data.get("username")

        if not telegram_id and not username:
            raise NotFound("Either telegram_id or username must be provided.")
        
        if telegram_id:
            user = get_object_or_404(User, telegram_id=telegram_id)
        else:
            user = get_object_or_404(User, username=username)
        
        return user
    
    def perform_update(self, serializer):
        """
        Updates the user's pray points and balance.

        Args:
            serializer (Serializer): The serializer containing validated data.
        """
        # The validated_data should have the pray instance
        user = self.get_object()
        points = serializer.validated_data['points']
        
        # Update the pray points and user balance
        user.balance += points
        user.save()

        # Update the level based on new points
        user.update_user_level()


    def update(self, request, *args, **kwargs):
        """
        Performs the update operation and returns the updated user instance.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: The serialized user data with updated points and balance.
        """
        # Perform the update
        response = super().update(request, *args, **kwargs)
        
        # Return the updated instance in the response
        return Response(self.get_serializer(self.get_object()).data)
    
# API: Task
# ----------------------------------------------------------------------------------------------
class TaskAPIView(ListAPIView, CreateAPIView, UpdateAPIView):
    """
    Manages CRUD operations for tasks.
    
    Attributes:
        permission_classes (list): List of permissions required for the view.
        queryset (QuerySet): Queryset for retrieving tasks.
        serializer_class (Serializer): Serializer for task data.
    """
    permission_classes = [IsAdminUser]
    queryset = Tasks.objects.all()
    serializer_class = TaskSerializer

# API: Card
# ----------------------------------------------------------------------------------------------
class CardAPIView(ListAPIView, CreateAPIView, UpdateAPIView):
    """
    Manages CRUD operations for cards.
    
    Attributes:
        permission_classes (list): List of permissions required for the view.
        queryset (QuerySet): Queryset for retrieving cards.
        serializer_class (Serializer): Serializer for card data.
    """
    permission_classes = [IsAdminUser]
    queryset = Cards.objects.all()
    serializer_class = CardSerializer

# API: CardDetails
# ----------------------------------------------------------------------------------------------
class CardDetailsAPIView(ListAPIView, CreateAPIView, UpdateAPIView):
    """
    Manages CRUD operations for card details.
    
    Attributes:
        permission_classes (list): List of permissions required for the view.
        queryset (QuerySet): Queryset for retrieving card details.
        serializer_class (Serializer): Serializer for card details data.
    """
    permission_classes = [IsAdminUser]
    queryset = CardsDetails.objects.all()
    serializer_class = CardDetailsSerializer