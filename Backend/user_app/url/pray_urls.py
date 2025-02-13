from django.urls import path
from user_app.view.pray_view import *

urlpatterns = [
    # UpdateBalance
    # ---------------------------------------------------------------------
    path("tma_masterverses/update-pray-points/", UpdateBalanceAPIView.as_view(), name="update-balance"),
    # UserEarnings
    # ---------------------------------------------------------------------
    path("earning/", UserEarningsAPIView.as_view(), name="user-earnings"),
    # UserRefferalLeaderboard
    # ---------------------------------------------------------------------
    path("my-refferal-leaderboard/", UserRefferalLeaderboardAPIView.as_view(), name="user-refferal-leaderboard"),
    # OverallLeaderboard
    # ---------------------------------------------------------------------
    path("overall-leaderboard/", OverallLeaderboardAPIView.as_view(), name="overall-leaderboard"),
    # RefferalLeaderboard
    # ---------------------------------------------------------------------
    path("refferal-leaderboard/", RefferalLeaderboardAPIView.as_view(), name="refferal-leaderboard"),
    # Tasks
    # ---------------------------------------------------------------------
    path("tasks/", TasksAPIView.as_view(), name="tasks"),
    # UserTaskClaim
    # ---------------------------------------------------------------------
    path("claim-task/", UserTaskClaimAPIView.as_view(), name="claim-task"),
    # Cards
    # ---------------------------------------------------------------------
    path("cards/", CardsAPIView.as_view(), name="cards-list"),
    # UserCardClaim
    # ---------------------------------------------------------------------
    path("claim-card/", UserCardClaimAPIView.as_view(), name="claim-card"),
    # UpdateUserCardLevel
    # ---------------------------------------------------------------------
    path("update-card-level/", UpdateUserCardLevelAPIView.as_view(), name="update-card-level"),
    # CardDetails
    # ---------------------------------------------------------------------
    path("card-details/", CardDetailsAPIView.as_view(), name="card-details"),

    path('booster-claims/', BoosterClaimView.as_view(), name='booster-claims'),
    path("get-daily-reward/", DailyRewardAPIView.as_view()),
    path("claim-daily-reward/", ClaimRewardAPIView.as_view()),
]