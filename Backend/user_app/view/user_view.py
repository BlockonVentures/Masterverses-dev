from user_app.utils import Util
from user_app.models import User
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from user_app.serializer.user_serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView, CreateAPIView, UpdateAPIView
from rest_framework.exceptions import ValidationError

# API: Login user
# -----------------------------------------------------------------------------------------
class LoginAPIView(CreateAPIView):
    """
    API view to handle user login and account creation. This view authenticates a user 
    based on their telegram_id, creates a new user if necessary, and returns JWT tokens.

    Attributes:
        queryset: A QuerySet of all User objects in the database.
        serializer_class: The serializer class used to validate and deserialize the input data.
    """
    queryset = User.objects.all()
    serializer_class = LoginSerializer

    def create(self, request, *args, **kwargs):
        """
        Handle POST request for user login or creation. Validates the provided data, 
        creates a new user if necessary, and returns JWT tokens.

        Args:
            request: The HTTP request object containing user data (e.g., telegram_id).
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A response containing the generated tokens or error message.
        """
        serializer = self.get_serializer(data=request.data) # Initialize serializer with request data
        try:
            serializer.is_valid(raise_exception=True) # Validate the serializer input
        except ValidationError as e:
            # If validation fails, return an error response with appropriate message
            error_detail = e.detail.get("telegram_id", ["An unknown error occurred."])[0]
            return Response({"error": error_detail}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.context.get('user')  # Retrieve the validated user from context
        # If user does not exist in the system, create a new user
        if not user:
            user = serializer.save()

        # Generate JWT tokens for the existing or newly created user
        tokens = Util.get_tokens_for_user(user)
        # Return the generated tokens in the response
        return Response(tokens, status=status.HTTP_200_OK)
    
# API: UserDetails
# -----------------------------------------------------------------------------------------
class UserDetailsAPIView(ListAPIView):
    """
    API view to retrieve user details. This view returns the authenticated user's data.
    
    Attributes:
        permission_classes: Specifies that the user must be authenticated to access this view.
        serializer_class: The serializer class used to serialize the user data.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetailsSerializer

    def list(self, request, *args, **kwargs):
        """
        Handle GET request to retrieve user details. Returns the authenticated user's details.

        Args:
            request: The HTTP request object, containing user information.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A response containing the serialized user data.
        """
        serializer = self.get_serializer(request.user) # Serialize the data for the authenticated user
        return Response(serializer.data, status=status.HTTP_200_OK) # Return the serialized data
    
# API: WelcomeBonus
# ----------------------------------------------------------------------------------------------
class WelcomeBonusAPIView(UpdateAPIView):
    """
    API view to handle the update of the user's welcome bonus. This view updates the user's 
    welcome bonus status and increases their balance when they receive the bonus.

    Attributes:
        permission_classes: Specifies that the user must be authenticated to access this view.
        serializer_class: The serializer class used to serialize the user's data.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = WelcomeBonusSerializer

    def get_object(self):
        """
        Retrieve the current user object. This method is used to get the user instance 
        to apply the welcome bonus.

        Returns:
            User: The user instance associated with the current request.
        """
        user = self.request.user # Retrieve the currently authenticated user
        return user
    
    def update(self, request, *args, **kwargs):
        """
        Handle PUT or PATCH request to update the user's welcome bonus status. 
        This method marks the bonus as received, adds points to the user's balance, 
        and saves the changes.

        Args:
            request: The HTTP request object, containing the necessary data to update.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A response indicating the success or failure of the operation.
        """
        instance = self.get_object() # Get the current user object to be updated

        # Serialize and validate the instance before updating
        serializer = self.get_serializer(instance)
        serializer.validate(instance)  # Validate the instance

        # Apply the welcome bonus update
        instance.welcome_bonus = True # Mark the welcome bonus as received
        instance.balance += 10000 # Add 10000 points to the user's balance
        instance.save() # Save the changes to the user instance

        # Return a success response
        return Response({"msg": "Pray Welcome Bonus updated successfully"}, status=status.HTTP_200_OK)
    
class UpdateReligionView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        serializer = UpdateReligionSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Religion updated successfully!", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)