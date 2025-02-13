from django.db import connection
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.timezone import now
from datetime import timedelta
from datetime import timedelta
from django.utils import timezone
from user_app.models import UserDailyReward
from rest_framework.exceptions import NotFound
from user_app.serializer.pray_serializers import *
from django.db.models import Window, F, functions, Count, Q, OuterRef,Subquery
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import UpdateAPIView, ListAPIView, CreateAPIView

# API: UpdateBalance
# -----------------------------------------------------------------------------------------
class UpdateBalanceAPIView(generics.UpdateAPIView):
    """
    API endpoint for updating the balance of the currently authenticated user.

    This view allows authenticated users to update their balance by providing a new 
    balance amount that is greater than the current balance.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateBalanceSerializer
    http_method_names = ["patch"]

    def get_object(self):
        """
        Retrieve the currently authenticated user.
        
        Returns:
            User instance representing the currently authenticated user.
        """
        return self.request.user
    
    # @swagger_auto_schema(
    #     request_body=UpdateBalanceSerializer,
    #     responses={
    #         201: openapi.Response(
    #             description="Balance updated successfully",
    #             schema=openapi.Schema(
    #                 type=openapi.TYPE_OBJECT,
    #                 properties={
    #                     "level_number": openapi.Schema(type=openapi.TYPE_INTEGER, description="User's current level number"),
    #                     "level_name": openapi.Schema(type=openapi.TYPE_STRING, description="User's current level name"),
    #                     "balance": openapi.Schema(type=openapi.TYPE_INTEGER, description="User's current balance"),
    #                 }
    #             )
    #         ),
    #         400: openapi.Schema(
    #             type=openapi.TYPE_OBJECT,
    #             properties={
    #                 "non_field_errors": openapi.Schema(
    #                     type=openapi.TYPE_ARRAY,
    #                     description="Updated amount should be greater than the current balance.",
    #                     items=openapi.Items(type=openapi.TYPE_STRING)  # Specify the type of items in the array
    #                 )
    #             }
    #         )
    #     }
    # )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
# API: UserEarnings
# ------------------------------------------------------------------------------------------
class UserEarningsAPIView(CreateAPIView):
    """
    API View for creating new user earnings records.

    Allows authenticated users to record their earnings.
    """
    queryset = Earnings.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = UserEarningsSerializer

    def perform_create(self, serializer):
        """
        Save the earning record for the current user.
        """
        # Associate the earnings entry with the current user
        return serializer.save(user=self.request.user)
    
# API: UserRefferalLeaderboard
# ------------------------------------------------------------------------------------------
class UserRefferalLeaderboardAPIView(ListAPIView):
    """
    API View for displaying the referral leaderboard.

    Ranks users referred by the current user based on their balance.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserRefferalLeaderboardSerializer

    def get_queryset(self):
        """
        Get the leaderboard of users referred by the authenticated user.

        Uses the DenseRank window function to rank users by balance.
        """
        user = self.request.user
        # Get referred users ranked by balance in descending order
        queryset = User.objects.filter(reffered_by=user.telegram_id).annotate(
            rank=Window(
                expression=functions.DenseRank(),
                order_by=F("balance").desc()
            )
        )
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        Return the referral leaderboard data.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
# API: OverallLeaderboard
# ------------------------------------------------------------------------------------------
class OverallLeaderboardAPIView(ListAPIView):
    """
    API View for displaying the overall leaderboard.

    Shows the top 1000 users ranked by balance and provides the current user's rank.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OverallLeaderboardSerializer

    def get_leaderboard(self):
        """
        Get the top 1000 users ranked by balance.
        """
        # Retrieve the top 1000 users ranked by balance
        return User.objects.annotate(
            rank=Window(
                expression=functions.DenseRank(),
                order_by=[
                    F('balance').desc(),
                    F('reffered_points').desc(),
                    F('date_joined').asc()
                ]
            )
        ).order_by('rank')[:1000]
    
    def get_user_rank(self, user):
        """
        Get the rank, balance, and first name details for the authenticated user.
        """
        query = '''
            WITH ranked_users AS (
                SELECT u.telegram_id,
                    u.username AS username,
                    u.first_name AS first_name,
                    u.balance AS balance,
                    u.reffered_points AS referral_count,
                    u.date_joined AS date_joined,
                    DENSE_RANK() OVER (
                        ORDER BY u.balance DESC, 
                                    u.reffered_points DESC, 
                                    u.date_joined ASC
                    ) AS rank
                FROM user_app_user u
            )
            SELECT username, first_name, balance, rank FROM ranked_users 
            WHERE telegram_id = %s
        '''
        with connection.cursor() as cursor:
            cursor.execute(query, [user.telegram_id])
            result = cursor.fetchone()
        return {
            "username": result[0],
            "first_name": result[1],
            "balance": result[2],
            "rank": result[3]
        }


    
    def list(self, request, *args, **kwargs):
        """
        Return the leaderboard and the current user's rank.
        """
        leaderboard = self.get_leaderboard()
        user_rank = self.get_user_rank(request.user)
        serializer = self.get_serializer(leaderboard, many=True)
        return Response({"leaderboard": serializer.data, "user_details": user_rank}, status=status.HTTP_200_OK)
    
# API: RefferalLeaderboard
# --------------------------------------------------------------------------------------------
class RefferalLeaderboardAPIView(ListAPIView):
    """
    API View for displaying the referral points leaderboard.
    Shows the top 1000 users ranked by referral points and provides the current user's rank.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RefferalLeaderboardSerializer

    def get_leaderboard(self):
        """
        Get the top 1000 users ranked by referral points.
        """
        # Top 1000 users by referred points
        return User.objects.annotate(
            rank=Window(
                expression=functions.DenseRank(),
                order_by=F('reffered_points').desc()
            )
        ).order_by('rank')[:1000]

    def get_user_rank(self, user):
        """
        Get the rank and referral points details for the authenticated user.
        """
        # Custom SQL query to get the rank and referred count
        query = '''
                WITH ranked_users AS (
                    SELECT telegram_id, reffered_points, 
                        DENSE_RANK() OVER (ORDER BY reffered_points DESC) AS rank
                    FROM user_app_user
                )
                SELECT rank FROM ranked_users 
                WHERE telegram_id = %s
            '''
        with connection.cursor() as cursor:
            cursor.execute(query, [user.telegram_id])
            result = cursor.fetchone()
        refferal_count = User.objects.filter(reffered_by=user.telegram_id).count()
        return {
            "username": user.username,
            "first_name": user.first_name,
            "reffered_points": user.reffered_points,
            "rank": result[0],
            "refferal_count": refferal_count
        }


    def list(self, request, *args, **kwargs):
        """
        Return the referral leaderboard and the current user's rank.
        """
        leaderboard = self.get_leaderboard()
        user_rank = self.get_user_rank(request.user)
        serializer = self.get_serializer(leaderboard, many=True)
        return Response({"leaderboard": serializer.data, "user_details": user_rank}, status=status.HTTP_200_OK)



    
# API: Tasks
# --------------------------------------------------------------------------------------------
class TasksAPIView(ListAPIView):
    """
    API View for listing available tasks for users.
    """
    permission_classes = [IsAuthenticated]
    queryset = Tasks.objects.all()
    serializer_class = TasksSerializer

# API: UserTaskClaim
# --------------------------------------------------------------------------------------------
class UserTaskClaimAPIView(CreateAPIView):
    """
    API View for claiming a task by a user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserTaskClaimSerializer

# API: Cards
# ---------------------------------------------------------------------------------------------
class CardsAPIView(ListAPIView):
    """
    API View for listing available cards for users.
    """
    permission_classes = [IsAuthenticated]
    queryset = Cards.objects.all()
    serializer_class = CardsSerializer

# API: UserCardClaim
# ---------------------------------------------------------------------------------------------
class UserCardClaimAPIView(CreateAPIView):
    """
    API View for claiming a card by a user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserCardClaimSerializer

# API: UpdateUserCardLevel
# ---------------------------------------------------------------------------------------------
class UpdateUserCardLevelAPIView(CreateAPIView):
    """
    API View for updating the card level of a user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateUserCardLevelSerializer

# API: CardDetails
# ---------------------------------------------------------------------------------------------
class CardDetailsAPIView(ListAPIView):
    """
    API View for retrieving details of a specific card and its level.

    Users must provide both `card_id` and `level_number` as query parameters.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CardDetailsSerializer

    def get_queryset(self):
        """
        Retrieve card details based on `card_id` and `level_number`.
        """
        # Extract query parameters
        card_id = self.request.query_params.get("card_id")
        level_number = self.request.query_params.get("level_number")

        # Validate parameters
        if not card_id or not level_number:
            raise NotFound("Both 'card_id' and 'level_number' are required.")

        try:
            level_number = int(level_number)
        except ValueError:
            raise NotFound("Invalid level_number.")

        # Filter cards by ID and level
        queryset = CardsDetails.objects.filter(card__id=card_id, level_number=level_number)

        if not queryset.exists():
            raise NotFound("Card details not found.")

        return queryset
    
class BoosterClaimView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        current_time = timezone.now()
        claims = BoosterClaim.objects.filter(
            user=user,
            claim_at__gte=current_time - timedelta(hours=2)
        ).order_by('claim_at')

        serializer = BoosterClaimSerializer(claims, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        claim_type = request.data.get('claim_type')

        # Check if user can claim again (every 2 hours)
        current_time = timezone.now()
        last_claim = BoosterClaim.objects.filter(
            user=user,
            claim_at__gte=current_time - timedelta(hours=2)
        ).last()

        if last_claim:
            return Response({"error": "You can only claim once every 2 hours."}, status=400)

        # Create new claim
        end_time = current_time + timedelta(hours=2)
        booster_claim = BoosterClaim.objects.create(
            user=user,
            claim_type=claim_type,
            end_time=end_time
        )

        serializer = BoosterClaimSerializer(booster_claim)
        return Response(serializer.data, status=201)
    
class DailyRewardAPIView(generics.ListAPIView):
    """
    API endpoint for listing daily rewards and their status based on the user's progress.
    
    Returns a list of daily rewards with their points and claim status. The claim status 
    is personalized based on the user's current progress in the reward system.
    """
    queryset = DailyReward.objects.all().order_by('day')
    serializer_class = DailyRewardSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        """
        Adds the user's daily reward status to the serializer context.

        This context is used in the serializer to determine the user's reward status for each day.
        If a UserDailyReward instance doesn't exist for the user, it's created.
        """
        user = self.request.user
        user_daily_reward, _ = UserDailyReward.objects.get_or_create(user=user)
        return {"user_daily_reward": user_daily_reward}
    
# View: ClaimReward
# -------------------------------------------------------------------------------------
class ClaimRewardAPIView(generics.UpdateAPIView):
    """
    API endpoint for claiming a daily reward.

    This view allows users to claim their daily rewards based on their current reward status.
    It updates the user's progress and adds points to their balance upon successful claim.
    """
    queryset = UserDailyReward.objects.all()
    serializer_class = ClaimRewardSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Retrieves or creates the UserDailyReward instance for the current user.

        If the user does not have an associated UserDailyReward, a new instance is created and returned.
        """
        user = self.request.user
        return UserDailyReward.objects.get_or_create(user=user)[0]