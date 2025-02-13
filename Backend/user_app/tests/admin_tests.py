from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from user_app.models import User, Tasks, Cards, CardsDetails
from uuid import uuid4
from rest_framework import status
from user_app.serializer.admin_serializers import (
    TaskSerializer, CardSerializer, CardDetailsSerializer
)

# Test: AdminLogin
# ------------------------------------------------------------------------------------------------------------------------
class AdminLoginAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a staff user (admin) and a regular user for testing
        cls.admin_user = User.objects.create_user(
            telegram_id=123456789,
            username="adminuser",
            first_name="Admin",
            password="adminpassword",
            is_staff=True  # Ensure the user has admin privileges
        )
        
        cls.regular_user = User.objects.create_user(
            telegram_id=987654321,
            username="regularuser",
            first_name="Regular",
            password="userpassword",
            is_staff=False  # This user is not an admin
        )

        cls.url = reverse("admin-login")  # Adjust the URL name if necessary

    def test_admin_login_success(self):
        """Test admin login with valid credentials."""
        data = {
            "telegram_id": self.admin_user.telegram_id,
            "password": "adminpassword"
        }
        
        response = self.client.post(self.url, data, format="json")
        
        # Check if the response status is HTTP 200 OK
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue("access" in response.data)
        self.assertTrue("refresh" in response.data)

    def test_admin_login_invalid_credentials(self):
        """Test admin login with invalid credentials."""
        data = {
            "telegram_id": self.admin_user.telegram_id,
            "password": "wrongpassword"  # Incorrect password
        }
        
        response = self.client.post(self.url, data, format="json")
        
        # Check if the response status is HTTP 400 Bad Request (validation error)
        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.data)

    def test_admin_login_non_admin(self):
        """Test login attempt with a non-admin user."""
        data = {
            "telegram_id": self.regular_user.telegram_id,
            "password": "userpassword"
        }
        
        response = self.client.post(self.url, data, format="json")
        
        # Check if the response status is HTTP 400 Bad Request (validation error)
        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.data)
        self.assertEqual(response.data["non_field_errors"][0], "Sorry, you are not an admin.")

    def test_admin_login_missing_telegram_id(self):
        """Test login with missing telegram_id."""
        data = {
            "password": "adminpassword"  # Missing telegram_id
        }
        
        response = self.client.post(self.url, data, format="json")
        
        # Check if the response status is HTTP 400 Bad Request (missing field)
        self.assertEqual(response.status_code, 400)
        self.assertIn("telegram_id", response.data)

    def test_admin_login_missing_password(self):
        """Test login with missing password."""
        data = {
            "telegram_id": self.admin_user.telegram_id  # Missing password
        }
        
        response = self.client.post(self.url, data, format="json")
        
        # Check if the response status is HTTP 400 Bad Request (missing field)
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.data)

# Test: AdminUpdatePrayPoints
# ------------------------------------------------------------------------------------------------------------------------
class AdminUpdatePrayPointsAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Create an admin user
        cls.admin_user = User.objects.create_user(
            telegram_id=123456789,
            username="adminuser",
            first_name="Admin",
            password="adminpassword",
            is_staff=True  # Admin privilege
        )
        
        # Create a regular user to update their points
        cls.regular_user = User.objects.create_user(
            telegram_id=987654321,
            username="regularuser",
            first_name="Regular"
        )

        cls.url = reverse("admin-update-pray-points")

    def setUp(self):
        # Set up the test client and authenticate the admin user
        self.client.force_authenticate(user=self.admin_user)
    
    def test_admin_update_pray_points_success_by_telegram_id(self):
        """Test that admin can update pray points using telegram_id."""
        data = {
            "telegram_id": self.regular_user.telegram_id,
            "points": 100
        }
                
        response = self.client.patch(self.url, data, format="json")
        
        # Check if the response status is HTTP 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Verify that the user's balance has been updated
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.balance, 100)

    def test_admin_update_pray_points_success_by_username(self):
        """Test that admin can update pray points using username."""
        data = {
            "username": self.regular_user.username,
            "points": 50
        }
                
        response = self.client.patch(self.url, data, format="json")
        
        # Check if the response status is HTTP 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Verify that the user's balance has been updated
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.balance, 50)

    def test_admin_update_pray_points_invalid_user(self):
        """Test that trying to update points for a non-existing user returns an error."""
        data = {
            "telegram_id": 999999999,  # Non-existing telegram_id
            "points": 100
        }
        
        response = self.client.patch(self.url, data, format="json")
        
        # Check if the response status is HTTP 404 Not Found
        self.assertEqual(response.status_code, 404)

    def test_admin_update_pray_points_missing_identifier(self):
        """Test that attempting to update points without providing telegram_id or username returns an error."""
        data = {
            "points": 100  # Missing telegram_id or username
        }
                
        response = self.client.patch(self.url, data, format="json")
        
        # Check if the response status is HTTP 404 Not Found (Validation error)
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "Either telegram_id or username must be provided.")

    def test_admin_update_pray_points_non_admin(self):
        """Test that a non-admin user cannot update pray points."""
        data = {
            "telegram_id": self.regular_user.telegram_id,
            "points": 100
        }

        self.client.logout()
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.patch(self.url, data, format="json")
        
        # Check if the response status is HTTP 403 Forbidden
        self.assertEqual(response.status_code, 403)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "You do not have permission to perform this action.")

    def test_admin_update_pray_points_invalid_points(self):
        """Test that points cannot be updated with a value less than 1."""
        data = {
            "telegram_id": self.regular_user.telegram_id,
            "points": 0  # Invalid points
        }
                
        response = self.client.patch(self.url, data, format="json")
        
        # Check if the response status is HTTP 400 Bad Request (Validation error)
        self.assertEqual(response.status_code, 400)
        self.assertIn("points", response.data)
        self.assertEqual(response.data["points"][0], "Ensure this value is greater than or equal to 1.")

# Test: Task
# ------------------------------------------------------------------------------------------------------------------------
class TaskAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up an admin user
        cls.admin_user = User.objects.create_user(
            telegram_id=12345,
            username="admin",
            first_name="Admin",
            password="adminpass",
            is_staff=True
        )
        
        # Create a few tasks for testing purposes
        cls.task1 = Tasks.objects.create(
            name="Daily Login",
            description="Earn points for daily login",
            task_type="daily",
            points=10,
            action="visit"
        )
        cls.task2 = Tasks.objects.create(
            name="Share on Social Media",
            description="Earn points for sharing on social media",
            task_type="social",
            points=15,
            action="join",
            is_telegram=True
        )

        # URLs
        cls.task_list_url = reverse("task-list")
        cls.task_detail_url = lambda pk: reverse("task-detail", args=[pk])

    def setUp(self):
        # Force authenticate the admin user for each test case
        self.client.force_authenticate(user=self.admin_user)

    def test_list_tasks(self):
        # Test retrieving a list of tasks
        response = self.client.get(self.task_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Check if both tasks are returned
        
        serialized_data = TaskSerializer([self.task1, self.task2], many=True).data
        self.assertEqual(response.data, serialized_data)

    def test_create_task(self):
        # Test creating a new task
        data = {
            "name": "Follow on Instagram",
            "description": "Earn points for following us on Instagram",
            "task_type": "social",
            "points": 20,
            "action": "visit",
            "is_telegram": False,
        }
        response = self.client.post(self.task_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tasks.objects.count(), 3)  # Confirm new task was created
        self.assertEqual(response.data["name"], data["name"])

    def test_create_task_invalid_data(self):
        # Test creating a task with invalid data (missing required field)
        data = {
            # Invalid, name is required
            "description": "Task without name",
            "task_type": "daily",
            "points": 10,
            "action": "visit",
        }
        response = self.client.post(self.task_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)  # Check if 'name' error is present

    def test_update_task(self):
        # Test updating an existing task
        data = {
            "name": "Updated Task Name",
            "description": "Updated description",
            "task_type": "daily",
            "points": 30,
            "action": "join",
            "is_telegram": True,
        }
        response = self.client.put(self.task_detail_url(self.task1.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        updated_task = Tasks.objects.get(id=self.task1.id)
        self.assertEqual(updated_task.name, data["name"])
        self.assertEqual(updated_task.points, data["points"])

    def test_update_task_partial(self):
        # Test partially updating an existing task
        data = {
            "name": "Partially Updated Name",
        }
        response = self.client.patch(self.task_detail_url(self.task2.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        updated_task = Tasks.objects.get(id=self.task2.id)
        self.assertEqual(updated_task.name, data["name"])  # Only name should be updated

    def test_update_task_invalid_data(self):
        # Test updating a task with invalid data
        data = {
            "name": "",  # Invalid name
            "task_type": "invalid_type",  # Invalid task type
            "points": -5,  # Invalid points (negative value)
        }
        response = self.client.put(self.task_detail_url(self.task1.id), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
        self.assertIn("task_type", response.data)
        self.assertIn("points", response.data)

    def test_delete_task(self):
        # Test deleting an existing task
        response = self.client.delete(self.task_detail_url(self.task1.id))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Tasks.objects.filter(id=self.task1.id).exists())

    def test_unauthorized_access(self):
        # Test accessing the API without admin permissions
        self.client.logout()  # Remove admin authentication
        response = self.client.get(self.task_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

# Test: Card
# ------------------------------------------------------------------------------------------------------------------------
class CardAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up an admin user
        cls.admin_user = User.objects.create_user(
            telegram_id=12345,
            username="admin",
            first_name="Admin",
            password="adminpass",
            is_staff=True
        )
        
        # Create a few cards for testing purposes
        cls.card1 = Cards.objects.create(
            name="Card of Eternals",
            number=1,
            card_type="eternals",
            description="An eternal card of great power."
        )
        cls.card2 = Cards.objects.create(
            name="Card of Divine",
            number=2,
            card_type="divine",
            description="A divine card with mystical abilities."
        )

        # URLs
        cls.card_list_url = reverse("card-list")
        cls.card_detail_url = lambda pk: reverse("card-detail", args=[pk])

    def setUp(self):
        # Force authenticate the admin user for each test case
        self.client.force_authenticate(user=self.admin_user)

    def test_list_cards(self):
        # Test retrieving a list of cards
        response = self.client.get(self.card_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Check if both cards are returned
        
        serialized_data = CardSerializer([self.card1, self.card2], many=True).data
        self.assertEqual(response.data, serialized_data)

    def test_create_card(self):
        # Test creating a new card
        data = {
            "name": "Card of Specials",
            "number": 3,
            "card_type": "specials",
            "description": "A special card with unique abilities."
        }
        response = self.client.post(self.card_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Cards.objects.count(), 3)  # Confirm new card was created
        self.assertEqual(response.data["name"], data["name"])

    def test_create_card_invalid_data(self):
        # Test creating a card with invalid data (missing required field)
        data = {
            "name": "",  # Invalid, name is required
            "number": -1,  # Invalid, must be positive
            "card_type": "invalid_type",  # Invalid, not in choices
        }
        response = self.client.post(self.card_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
        self.assertIn("number", response.data)
        self.assertIn("card_type", response.data)

    def test_update_card(self):
        # Test updating an existing card
        data = {
            "name": "Updated Card Name",
            "number": 5,
            "card_type": "divine",
            "description": "Updated description for the card.",
        }
        response = self.client.put(self.card_detail_url(self.card1.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        updated_card = Cards.objects.get(id=self.card1.id)
        self.assertEqual(updated_card.name, data["name"])
        self.assertEqual(updated_card.number, data["number"])

    def test_update_card_partial(self):
        # Test partially updating an existing card
        data = {
            "name": "Partially Updated Card Name",
        }
        response = self.client.patch(self.card_detail_url(self.card2.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        updated_card = Cards.objects.get(id=self.card2.id)
        self.assertEqual(updated_card.name, data["name"])  # Only name should be updated

    def test_update_card_invalid_data(self):
        # Test updating a card with invalid data
        data = {
            "name": "",  # Invalid name
            "number": -5,  # Invalid number (negative value)
            "card_type": "nonexistent_type",  # Invalid card type
        }
        response = self.client.put(self.card_detail_url(self.card1.id), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
        self.assertIn("number", response.data)
        self.assertIn("card_type", response.data)

    def test_unauthorized_access(self):
        # Test accessing the API without admin permissions
        self.client.logout()  # Remove admin authentication
        response = self.client.get(self.card_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

# Test: CardDetails
# ------------------------------------------------------------------------------------------------------------------------
class CardDetailsAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up an admin user
        cls.admin_user = User.objects.create_user(
            telegram_id=12345,
            username="admin",
            first_name="Admin",
            password="adminpass",
            is_staff=True
        )
        
        # Create a card for testing purposes
        cls.card = Cards.objects.create(
            name="Card of Eternals",
            number=1,
            card_type="eternals",
            description="An eternal card of great power."
        )
        
        # Create a few card details for testing purposes
        cls.card_detail1 = CardsDetails.objects.create(
            card=cls.card,
            level_number=1,
            burning_points=100,
            automine_points=50
        )
        cls.card_detail2 = CardsDetails.objects.create(
            card=cls.card,
            level_number=2,
            burning_points=200,
            automine_points=150
        )

        # URLs
        cls.card_details_list_url = reverse("carddetails-list")
        cls.card_details_detail_url = lambda pk: reverse("carddetails-detail", args=[pk])

    def setUp(self):
        # Force authenticate the admin user for each test case
        self.client.force_authenticate(user=self.admin_user)

    def test_list_card_details(self):
        # Test retrieving a list of card details
        response = self.client.get(self.card_details_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Check if both card details are returned
        
        serialized_data = CardDetailsSerializer([self.card_detail1, self.card_detail2], many=True).data
        self.assertEqual(response.data, serialized_data)

    def test_create_card_detail(self):
        # Test creating a new card detail
        data = {
            "card": self.card.id,
            "level_number": 3,
            "burning_points": 300,
            "automine_points": 200
        }
        response = self.client.post(self.card_details_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CardsDetails.objects.count(), 3)  # Confirm new card detail was created
        self.assertEqual(response.data["level_number"], data["level_number"])

    def test_create_card_detail_invalid_data(self):
        # Test creating a card detail with invalid data (missing required fields)
        data = {
            "card": "",  # Invalid, card ID is required
            "level_number": -1,  # Invalid, must be positive
            "burning_points": "invalid",  # Invalid, should be an integer
        }
        response = self.client.post(self.card_details_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("card", response.data)
        self.assertIn("level_number", response.data)
        self.assertIn("burning_points", response.data)

    def test_update_card_detail(self):
        # Test updating an existing card detail
        data = {
            "card": self.card.id,
            "level_number": 5,
            "burning_points": 500,
            "automine_points": 300
        }
        response = self.client.put(self.card_details_detail_url(self.card_detail1.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        updated_card_detail = CardsDetails.objects.get(id=self.card_detail1.id)
        self.assertEqual(updated_card_detail.level_number, data["level_number"])
        self.assertEqual(updated_card_detail.burning_points, data["burning_points"])

    def test_update_card_detail_partial(self):
        # Test partially updating an existing card detail
        data = {
            "burning_points": 700,
        }
        response = self.client.patch(self.card_details_detail_url(self.card_detail2.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        updated_card_detail = CardsDetails.objects.get(id=self.card_detail2.id)
        self.assertEqual(updated_card_detail.burning_points, data["burning_points"])  # Only burning points should be updated

    def test_update_card_detail_invalid_data(self):
        # Test updating a card detail with invalid data
        data = {
            "level_number": -2,  # Invalid level number
            "burning_points": "invalid",  # Invalid burning points (string instead of int)
            "automine_points": -50  # Invalid automine points (negative)
        }
        response = self.client.put(self.card_details_detail_url(self.card_detail1.id), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("level_number", response.data)
        self.assertIn("burning_points", response.data)
        self.assertIn("automine_points", response.data)

    def test_unauthorized_access(self):
        # Test accessing the API without admin permissions
        self.client.logout()  # Remove admin authentication
        response = self.client.get(self.card_details_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)