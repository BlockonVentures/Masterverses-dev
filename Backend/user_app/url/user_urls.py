from django.urls import path
from user_app.view.user_view import *

urlpatterns = [
    # Login
    # ---------------------------------------------------------------------
    path("login/", LoginAPIView.as_view(), name="login"),
    # UserDetails
    # ---------------------------------------------------------------------
    path("user-details/", UserDetailsAPIView.as_view(), name="user-details"),
    # WelcomeBonus
    # --------------------------------------------------------------------
    path("welcome-bonus/", WelcomeBonusAPIView.as_view(), name="welcome-bonus"),
    path("update-religion/", UpdateReligionView.as_view(), name="update-religion"),

]