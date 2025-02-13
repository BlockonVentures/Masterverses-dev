from django.urls import path
from user_app.view.admin_view import *

urlpatterns = [
    # Admin Login
    # ---------------------------------------------------------------------
    path("admin/login/", AdminLoginAPIView.as_view(), name="admin-login"),
    # AdminUpdatePrayPoints
    # ---------------------------------------------------------------------
    path("admin/update-pray-points/", AdminUpdatePrayPointsAPIView.as_view(), name="admin-update-pray-points"),
    # Task
    # ---------------------------------------------------------------------
    path("admin/task/", TaskAPIView.as_view(), name="task-list"),
    path("admin/task/<uuid:pk>/", TaskAPIView.as_view(), name="task-detail"),
    # Card
    # ---------------------------------------------------------------------
    path("admin/card/", CardAPIView.as_view(), name="card-list"),
    path("admin/card/<uuid:pk>/", CardAPIView.as_view(), name="card-detail"),
    # CardDetails
    # ---------------------------------------------------------------------
    path("admin/card-details/", CardDetailsAPIView.as_view(), name="carddetails-list"),
    path("admin/card-details/<int:pk>/", CardDetailsAPIView.as_view(), name="carddetails-detail"),
]