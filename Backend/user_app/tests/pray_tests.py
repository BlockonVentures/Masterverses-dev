from uuid import uuid4
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from unittest import mock
from django.utils import timezone
from user_app.models import (
    Rules, User, Tasks, UserTaskClaim, Cards, CardsDetails, UserCardClaim
)

# Test: UpdateBalance
# ------------------------------------------------------------------------------------------------------------------------
class UpdateBalanceAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Set up test data that will be shared across tests, including
        creating a user and sample rules for level calculation.
        """
        # Create a test user
        cls.user = User.objects.create_user(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            balance=100,  # Initial balance
            level_number=1,
            level_name="Seeker of Truth"
        )

        # Create level thresholds in the Rules model
        cls.rule_level_1 = Rules.objects.create(
            level_number=1,
            level_name="Seeker of Truth",
            lower_points=0,
            higher_points=100,
            per_tap=10,
            point_refill=50,
            number_of_tap=5
        )
        
        cls.rule_level_2 = Rules.objects.create(
            level_number=2,
            level_name="Knowledge Seeker",
            lower_points=101,
            higher_points=200,
            per_tap=15,
            point_refill=75,
            number_of_tap=7
        )

        cls.url = reverse("update-balance")

    def setUp(self):
        """
        Authenticate the user before each test.
        """
        self.client.force_authenticate(user=self.user)

    def test_update_balance_success(self):
        """
        Ensure the balance is updated successfully when providing a valid value greater than the current balance.
        """
        data = {"balance": 150}
        response = self.client.put(self.url, data, format="json")
        
        # Ensure the response status is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if the balance was updated correctly
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, data["balance"])
        
        # Verify the response data matches the updated balance
        self.assertEqual(response.data["balance"], data["balance"])

    def test_update_balance_triggers_level_update(self):
        """
        Verify that updating the balance also triggers an update in user level when balance reaches new threshold.
        """
        data = {"balance": 150}  # Above initial balance and within the level 2 threshold
        response = self.client.put(self.url, data, format="json")

        # Reload the user instance to get updated data
        self.user.refresh_from_db()

        # Check if the level has updated according to the Rules model
        self.assertEqual(self.user.level_number, 2)
        self.assertEqual(self.user.level_name, "Knowledge Seeker")

    def test_update_balance_insufficient_value(self):
        """
        Ensure that an update fails if the balance is set to a value less than or equal to the current balance.
        """
        data = {"balance": 50}  # Less than the current balance of 100
        response = self.client.put(self.url, data, format="json")
        
        # Check if the status is 400 Bad Request due to validation error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify the error message
        self.assertIn("Updated points cannot be less than or equal to the current points", response.data["balance"])

    def test_update_balance_unauthenticated(self):
        """
        Ensure that an unauthenticated request is denied.
        """
        self.client.logout()  # Log out the authenticated user
        data = {"balance": 150}
        response = self.client.put(self.url, data, format="json")
        
        # Check if the response status is 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_balance_invalid_data(self):
        """
        Ensure that the API handles invalid data gracefully.
        """
        data = {"balance": "invalid"}  # Pass a non-integer balance
        response = self.client.put(self.url, data, format="json")
        
        # Check if the response status is 400 Bad Request due to invalid data
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Confirm there's an error message in response
        self.assertIn("balance", response.data)

    def test_update_balance_no_data(self):
        """
        Ensure that the API returns an error when no data is provided.
        """
        response = self.client.put(self.url, {}, format="json")
        
        # Check if the response status is 400 Bad Request due to missing data
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Confirm there's an error message for the balance field
        self.assertIn("balance", response.data)
        self.assertEqual(response.data["balance"][0].code, "required")

    def test_update_balance_level_update_called(self):
        """
        Ensure that updating the balance triggers a level update for the user.
        """
        # Mock the update_user_level method
        with mock.patch.object(User, 'update_user_level', return_value=None) as mock_update_level:
            data = {"balance": 200}  # Valid update value
            response = self.client.put(self.url, data, format="json")
            
            # Ensure that level update was called during balance update
            mock_update_level.assert_called_once()

# Test: UserEarnings
# ------------------------------------------------------------------------------------------------------------------------
class UserEarningsAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Set up shared test data for user and initial earnings rules.
        """
        cls.user = User.objects.create_user(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            balance=500,  # Initial balance for DEBIT transactions
            multitap_level=5,
            recharging_speed_level=5,
            autobot_status=False
        )
        
        cls.url = reverse("user-earnings")  # Update with the actual name if set in urls.py

    def setUp(self):
        """
        Authenticate the user before each test.
        """
        self.client.force_authenticate(user=self.user)

    def test_create_credit_transaction_success(self):
        """
        Ensure a CREDIT transaction increases the user's balance.
        """
        data = {
            "amount": 100,
            "transaction_type": "CREDIT",
            "reason": "Bonus"
        }
        response = self.client.post(self.url, data, format="json")
        
        # Check if the response status is 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Reload the user instance and check if the balance is updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, 600)  # Initial 500 + 100 CREDIT

    def test_create_debit_transaction_success(self):
        """
        Ensure a DEBIT transaction decreases the user's balance.
        """
        data = {
            "amount": 100,
            "transaction_type": "DEBIT",
            "reason": "Purchase"
        }
        response = self.client.post(self.url, data, format="json")
        
        # Check if the response status is 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Reload the user instance and check if the balance is updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, 500)  # Initial 600 - 100 DEBIT

    def test_debit_transaction_insufficient_funds(self):
        """
        Ensure a DEBIT transaction fails if the user does not have enough funds.
        """
        data = {
            "amount": 600,
            "transaction_type": "DEBIT",
            "reason": "Purchase"
        }
        response = self.client.post(self.url, data, format="json")
        
        # Check if the response status is 400 Bad Request due to insufficient funds
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Confirm that the error message indicates insufficient funds
        self.assertIn("Insufficient Funds", str(response.data))

    def test_debit_transaction_increases_multitap_level(self):
        """
        Ensure that a DEBIT transaction for 'Mutitap Increase' deducts the balance and increases multitap level.
        """
        data = {
            "amount": 100,
            "transaction_type": "DEBIT",
            "reason": "Mutitap Increase"
        }
        response = self.client.post(self.url, data, format="json")
        
        # Check if the response status is 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Reload the user instance and check if the balance and multitap level are updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, 400)  # Initial 500 - 100 DEBIT
        self.assertEqual(self.user.multitap_level, 6)  # Initial 5 + 1

    def test_debit_transaction_increases_recharging_speed_level(self):
        """
        Ensure that a DEBIT transaction for 'Recharging Speed Increase' deducts the balance and increases recharging speed level.
        """
        data = {
            "amount": 100,
            "transaction_type": "DEBIT",
            "reason": "Recharging Speed Increase"
        }
        response = self.client.post(self.url, data, format="json")
        
        # Check if the response status is 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Reload the user instance and check if the balance and recharging speed level are updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, 400)  # Initial 500 - 100 DEBIT
        self.assertEqual(self.user.recharging_speed_level, 6)  # Initial 5 + 1

    def test_debit_transaction_activates_autobot(self):
        """
        Ensure that a DEBIT transaction for 'Auto Pray' deducts the balance and activates the autobot.
        """
        data = {
            "amount": 100,
            "transaction_type": "DEBIT",
            "reason": "Auto Pray"
        }
        response = self.client.post(self.url, data, format="json")
        
        # Check if the response status is 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Reload the user instance and check if the balance is updated and autobot is activated
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, 400)  # Initial 500 - 100 DEBIT
        self.assertTrue(self.user.autobot_status)

    def test_create_earning_unauthenticated(self):
        """
        Ensure an unauthenticated user cannot create an earnings entry.
        """
        self.client.logout()  # Log out the authenticated user
        data = {
            "amount": 100,
            "transaction_type": "CREDIT",
            "reason": "Bonus"
        }
        response = self.client.post(self.url, data, format="json")
        
        # Check if the response status is 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)

# Test: UserRefferalLeaderboard
# ------------------------------------------------------------------------------------------------------------------------
class UserRefferalLeaderboardAPITest(APITestCase):
    """
    Test suite for the UserRefferalLeaderboard API.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Set up initial data for the referral leaderboard tests.
        """
        # Create the main user who refers others
        cls.main_user = User.objects.create_user(
            telegram_id=1111,
            username="mainuser",
            first_name="Main",
            balance=500
        )

        # Create users referred by the main user with varying balances
        cls.referred_users = [
            User.objects.create_user(
                telegram_id=1112 + i,
                username=f"referred_user_{i}",
                first_name=f"Referred {i}",
                reffered_by=cls.main_user.telegram_id,
                balance=1000 - (i * 200)  # Decreasing balance for rank
            )
            for i in range(5)
        ]

        # Define the API URL
        cls.url = reverse("user-refferal-leaderboard")

    def setUp(self):
        """
        Authenticate the user before each test.
        """
        self.client.force_authenticate(user=self.main_user)

    def test_leaderboard_success(self):
        """
        Ensure that the leaderboard is retrieved successfully with correct data.
        """
        response = self.client.get(self.url)
        
        # Check the response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify the correct number of referred users are returned
        self.assertEqual(len(response.data), len(self.referred_users))

        # Check that the users are ranked correctly by balance in descending order
        expected_ranking = sorted(
            self.referred_users, key=lambda user: user.balance, reverse=True
        )
        for index, user_data in enumerate(response.data):
            self.assertEqual(user_data["username"], expected_ranking[index].username)
            self.assertEqual(user_data["rank"], index + 1)

    def test_unauthenticated_access(self):
        """
        Ensure unauthenticated users cannot access the leaderboard.
        """
        self.client.logout()  # Log out the authenticated user
        response = self.client.get(self.url)

        # Check if the response status is 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

# Test: OverallLeaderboard
# ------------------------------------------------------------------------------------------------------------------------
class OverallLeaderboardAPITest(APITestCase):
    """
    Test suite for the OverallLeaderboard API.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Set up shared test data for leaderboard and user rank.
        """
        # Create multiple users with varying balances
        cls.users = [
            User.objects.create_user(
                telegram_id=1000 + i,
                username=f"user_{i}",
                first_name=f"User {i}",
                balance=2000 - i  # Decreasing balance for rank
            )
            for i in range(1050)  # More than 1000 to test ranking cutoff
        ]

        # Set the authenticated user
        cls.auth_user = cls.users[500]  # Middle of the pack
        cls.url = reverse("overall-leaderboard")  # Ensure the URL is named properly

    def setUp(self):
        """
        Authenticate the user before each test.
        """
        self.client.force_authenticate(user=self.auth_user)

    def test_overall_leaderboard_success(self):
        """
        Ensure the leaderboard and current user rank are returned successfully.
        """
        response = self.client.get(self.url)
        
        # Check the response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify leaderboard contains at most 1000 users
        leaderboard = response.data["leaderboard"]
        self.assertEqual(len(leaderboard), 1000)

        # Check if the leaderboard is sorted by balance in descending order
        balances = [user["balance"] for user in leaderboard]
        self.assertEqual(balances, sorted(balances, reverse=True))

        # Verify user rank details
        user_details = response.data["user_details"]
        self.assertEqual(user_details["username"], self.auth_user.username)
        self.assertEqual(user_details["balance"], self.auth_user.balance)

        # Ensure rank is correct based on balance
        expected_rank = User.objects.filter(balance__gt=self.auth_user.balance).count() + 1
        self.assertEqual(user_details["rank"], expected_rank)

    def test_user_outside_top_1000(self):
        """
        Ensure that a user outside the top 1000 receives their correct rank.
        """
        low_rank_user = self.users[-1]  # User with lowest balance
        self.client.force_authenticate(user=low_rank_user)
        
        response = self.client.get(self.url)
        
        # Check if the response status is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that the user is not in the leaderboard but rank is provided
        leaderboard_user_ids = [user["telegram_id"] for user in response.data["leaderboard"]]
        self.assertNotIn(low_rank_user.telegram_id, leaderboard_user_ids)

        user_details = response.data["user_details"]
        self.assertEqual(user_details["username"], low_rank_user.username)
        self.assertEqual(user_details["balance"], low_rank_user.balance)
        self.assertEqual(
            user_details["rank"],
            User.objects.filter(balance__gt=low_rank_user.balance).count() + 1
        )

    def test_unauthenticated_access(self):
        """
        Ensure unauthenticated users cannot access the leaderboard.
        """
        self.client.logout()  # Log out the authenticated user
        response = self.client.get(self.url)

        # Check if the response status is 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

# Test: RefferalLeaderboard
# ------------------------------------------------------------------------------------------------------------------------
class RefferalLeaderboardAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Create 1050 users with referral points varying from 10000 to 0
        cls.users = [
            User.objects.create_user(
                telegram_id=1000 + i,
                username=f"user_{i}",
                first_name=f"User {i}",
                reffered_points=10000 - i  # Referred points decrease per user
            )
            for i in range(1050)
        ]
        
        # Assign 5 users to be referred by the first user
        for i in range(5):
            cls.users[10 + i].reffered_by = cls.users[0].telegram_id
            cls.users[10 + i].save()
        
        cls.url = reverse("refferal-leaderboard")

    def authenticate_user(self, user):
        self.client.force_authenticate(user=user)

    def test_get_referral_leaderboard_success(self):
        """
        Test fetching the referral leaderboard for authenticated user.
        """
        self.authenticate_user(self.users[0])
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("leaderboard", response.data)
        self.assertIn("user_details", response.data)
        self.assertEqual(len(response.data["leaderboard"]), 1000)

    def test_user_rank_in_leaderboard(self):
        """
        Test to ensure authenticated user's rank and referred points are correct.
        """
        self.authenticate_user(self.users[0])
        response = self.client.get(self.url)

        user_details = response.data["user_details"]
        self.assertEqual(user_details["username"], "user_0")
        self.assertEqual(user_details["reffered_points"], 10000)
        self.assertEqual(user_details["rank"], 1)
        self.assertEqual(user_details["refferal_count"], 5)

    def test_user_not_in_top_1000(self):
        """
        Test to ensure users outside top 1000 are not included in leaderboard.
        """
        self.authenticate_user(self.users[1049])  # User with lowest referral points
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.users[1049].username, [user["username"] for user in response.data["leaderboard"]])

    def test_unauthenticated_user(self):
        """
        Test accessing the leaderboard without authentication.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

# Test: Tasks
# ------------------------------------------------------------------------------------------------------------------------
class TasksAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test user
        cls.user = User.objects.create_user(
            telegram_id=1000,
            username="user_1",
            first_name="User One",
            balance=5000,
            reffered_points=1500
        )
        
        # Create some tasks
        cls.daily_task = Tasks.objects.create(
            name="Daily Task 1",
            description="Complete the daily task",
            task_type="daily",
            points=100,
            action="join",
        )
        
        cls.social_task = Tasks.objects.create(
            name="Social Task 1",
            description="Complete the social task",
            task_type="social",
            points=200,
            action="visit",
        )
        
        # Create task claims
        UserTaskClaim.objects.create(
            user=cls.user,
            task=cls.daily_task,
            date_claimed=timezone.now()
        )

        cls.url = reverse("tasks")

    def authenticate_user(self, user):
        self.client.force_authenticate(user=user)

    def test_get_tasks_list_success(self):
        """
        Test fetching tasks list for an authenticated user.
        """
        self.authenticate_user(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
        self.assertIn("id", response.data[0])
        self.assertIn("name", response.data[0])

    def test_get_task_claim_status(self):
        """
        Test the claim status of the tasks for an authenticated user.
        """
        self.authenticate_user(self.user)
        response = self.client.get(self.url)
        
        tasks = response.data
        # Check if the daily task claim is marked as True (since user has already claimed it)
        daily_task = next(task for task in tasks if task["name"] == "Daily Task 1")
        self.assertTrue(daily_task["claim"])

        # Check if the social task claim is marked as False (user has not claimed it yet)
        social_task = next(task for task in tasks if task["name"] == "Social Task 1")
        self.assertFalse(social_task["claim"])

    def test_get_task_image_url(self):
        """
        Test that the image URL for the task is returned as HTTPS.
        """
        self.authenticate_user(self.user)

        # Create a task with an image
        task_with_image = Tasks.objects.create(
            name="Image Task",
            description="Task with an image",
            task_type="social",
            points=50,
            action="join",
            image="path/to/image.jpg"  # Mock image path
        )
        response = self.client.get(self.url)

        task = next(task for task in response.data if task["name"] == "Image Task")
        self.assertTrue(task["image"].startswith("https://"))
    
    def test_unauthenticated_user(self):
        """
        Test that unauthenticated users cannot access the tasks list.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @mock.patch('user_app.models.UserTaskClaim.objects.filter')
    def test_claim_status_for_non_existent_task(self, mock_claim_check):
        """
        Test task claim status for a task that has not been claimed.
        """
        mock_claim_check.return_value.exists.return_value = False
        task = Tasks.objects.create(
            name="New Task",
            description="A new task",
            task_type="daily",
            points=500,
            action="join",
        )
        self.authenticate_user(self.user)
        response = self.client.get(self.url)

        task_data = next(t for t in response.data if t["name"] == "New Task")
        self.assertFalse(task_data["claim"])

# Test: UserTaskClaim
# ------------------------------------------------------------------------------------------------------------------------
class UserTaskClaimAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a test user
        cls.user = User.objects.create_user(
            telegram_id=1001,
            username="user_1",
            first_name="User One",
            balance=1000,
            reffered_points=100
        )
        
        # Create a test task
        cls.task = Tasks.objects.create(
            name="Daily Task 1",
            description="Complete the daily task",
            task_type="daily",
            points=100,
            action="join",
        )
        
        cls.url = reverse("claim-task")
    
    def authenticate_user(self, user):
        self.client.force_authenticate(user=user)

    def test_claim_task_success(self):
        """
        Test claiming a task successfully and updating user balance.
        """
        self.authenticate_user(self.user)

        data = {"id": str(self.task.id)}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.user.balance, 1100)  # balance should increase by task points

        # Check the response
        self.assertEqual(response.data["claim"], True)
        self.assertEqual(response.data["name"], self.task.name)
        self.assertEqual(response.data["description"], self.task.description)
        self.assertEqual(response.data["task_type"], self.task.task_type)
        self.assertEqual(response.data["points"], self.task.points)

    def test_claim_task_already_claimed_daily(self):
        """
        Test trying to claim a daily task that has already been claimed today.
        """
        self.authenticate_user(self.user)

        # Claim the task once
        UserTaskClaim.objects.create(user=self.user, task=self.task, date_claimed=timezone.now(), claimed=True)
        
        data = {"id": str(self.task.id)}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["non_field_errors"][0], "Task already claimed today.")

    def test_claim_task_already_claimed_social(self):
        """
        Test trying to claim a social task that has already been claimed.
        """
        # Change task type to social for this test
        self.task.task_type = "social"
        self.task.save()

        self.authenticate_user(self.user)

        # Claim the task once
        UserTaskClaim.objects.create(user=self.user, task=self.task, claimed=True)
        
        data = {"id": str(self.task.id)}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["non_field_errors"][0], "Task Already Claimed.")

    def test_claim_task_nonexistent(self):
        """
        Test claiming a task with a non-existent ID.
        """
        self.authenticate_user(self.user)

        data = {"id": "496a685b-c245-4c7a-a464-92e7a09bf977"}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["id"][0], "Not a Valid Task ID")

    def test_unauthenticated_user(self):
        """
        Test that unauthenticated users cannot claim tasks.
        """
        data = {"id": str(self.task.id)}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

# Test: Cards
# ------------------------------------------------------------------------------------------------------------------------
class CardsAPIViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Creating a test user
        cls.user = User.objects.create_user(
            telegram_id='12345',
            username="testUser",
            first_name="Test",
            level_number=2
        )
        
        # Creating test cards
        cls.card1 = Cards.objects.create(
            name="Eternal Flame", 
            number=1, 
            card_type="eternals",
            description="Flame of eternity",
            image=None
        )
        cls.card2 = Cards.objects.create(
            name="Divine Radiance", 
            number=2, 
            card_type="divine",
            description="Radiance from the divine",
            image=None
        )

        cls.url = reverse("cards-list") 

    def setUp(self):
        # Authenticate the user using force_authenticate
        self.client.force_authenticate(user=self.user)
    
    def test_cards_api_view(self):        
        # Making a GET request to the cards API
        response = self.client.get(self.url)
        
        # Assert that the response status is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that the response contains the correct card details
        response_data = response.data
        self.assertEqual(len(response_data), 2)  # Since we created 2 cards
        
        # Check if card names are included in the response
        card_names = [card["name"] for card in response_data]
        self.assertIn(self.card1.name, card_names)
        self.assertIn(self.card2.name, card_names)
        
        # Check if each card's 'claim' field is in the response
        self.assertTrue("claim" in response_data[0])
        self.assertTrue("claim" in response_data[1])
        
        # Check if the 'level' field is in the response
        self.assertTrue("level" in response_data[0])
        self.assertTrue("level" in response_data[1])
        
        # Check that the 'status' field is either "claimed", "unlocked" or "locked"
        valid_statuses = ["claimed", "unlocked", "locked"]
        for card in response_data:
            self.assertIn(card["status"], valid_statuses)

        # Assert that burning and automine points are being returned correctly
        self.assertTrue("burning_points" in response_data[0])
        self.assertTrue("automine_points" in response_data[0])

    def test_unauthenticated_access(self):
        # Try to access the cards API without authentication
        self.client.logout()  # Log out the authenticated user
        
        url = reverse("cards-list")  # Assuming 'cards-list' is the name of your URL pattern
        response = self.client.get(url)
        
        # Assert that the status code is 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

# Test: UserCardClaim
# ------------------------------------------------------------------------------------------------------------------------
class UserCardClaimAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up initial test data
        cls.user = User.objects.create_user(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            balance=1000
        )
        cls.card = Cards.objects.create(name="Test Card", number=1, card_type="eternals")
        cls.card_details = CardsDetails.objects.create(
            card=cls.card,
            level_number=0,
            burning_points=200,
            automine_points=10
        )
        
        # URL for claiming the card
        cls.url = reverse("claim-card")

    def setUp(self):
        # Set up the test client and authenticate the user
        self.client.force_authenticate(user=self.user)

    def test_claim_card_success(self):
        """
        Test that a user can successfully claim a card if they have enough balance and the card is not already claimed.
        """
        data = {
            "id": str(self.card.id),
            "burning_points": 200
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, 800)  # Balance after deducting burning points
        self.assertTrue(UserCardClaim.objects.filter(user=self.user, card=self.card).exists())
        self.assertEqual(response.data["status"], "claimed")

    def test_claim_card_insufficient_balance(self):
        """
        Test that a user cannot claim a card if they have insufficient balance.
        """
        self.user.balance = 100  # Set balance lower than required burning points
        self.user.save()
        data = {
            "id": str(self.card.id),
            "burning_points": 200
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Insufficients Funds", response.data["non_field_errors"][0])

    def test_claim_card_already_claimed(self):
        """
        Test that a user cannot claim a card that they have already claimed.
        """
        # Create an existing claim
        UserCardClaim.objects.create(user=self.user, card=self.card, claimed=True)
        data = {
            "id": str(self.card.id),
            "burning_points": 200
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Already Claimed", response.data["non_field_errors"][0])

    def test_claim_invalid_card_id(self):
        """
        Test that a user cannot claim a card with an invalid card ID.
        """
        data = {
            "id": "00000000-0000-0000-0000-000000000000",  # Non-existing UUID
            "burning_points": 200
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Not a valid Card ID", response.data["id"][0])

    def test_claim_card_unauthenticated(self):
        """
        Test that an unauthenticated user cannot claim a card.
        """
        self.client.logout()
        data = {
            "id": str(self.card.id),
            "burning_points": 200
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

# Test: UpdateCardLevel
# ------------------------------------------------------------------------------------------------------------------------
class UpdateUserCardLevelAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up initial test data
        cls.user = User.objects.create_user(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            balance=1000
        )
        cls.card = Cards.objects.create(name="Test Card", number=1, card_type="eternals")

        # Create multiple CardsDetails instances for various levels
        for level in range(1, 12):  # Levels from 1 to 11
            CardsDetails.objects.create(
                card=cls.card,
                level_number=level,
                burning_points=level * 100,  # Varying burning points for each level
                automine_points=level * 10   # Varying automine points for each level
            )

        # Claim the card at level 1
        cls.user_card_claim = UserCardClaim.objects.create(
            user=cls.user,
            card=cls.card,
            card_level=1,
            claimed=True
        )

        # URL for updating the card level
        cls.url = reverse("update-card-level")

    def setUp(self):
        # Set up the test client and authenticate the user
        self.client.force_authenticate(user=self.user)

    def test_update_card_level_success(self):
        """
        Test that a user can successfully update the card level if they have enough balance and the card level has not reached the limit.
        """
        data = {
            "id": str(self.card.id),
            "points": 200
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.user.refresh_from_db()
        self.user_card_claim.refresh_from_db()
        self.assertEqual(self.user.balance, 800)  # Balance after deducting points
        self.assertEqual(self.user_card_claim.card_level, 2)  # Level incremented by 1
        self.assertEqual(response.data["level"], 2)
        self.assertEqual(response.data["status"], "claimed")

    def test_update_card_level_insufficient_balance(self):
        """
        Test that a user cannot update the card level if they have insufficient balance.
        """
        self.user.balance = 100  # Set balance lower than required points
        self.user.save()
        data = {
            "id": str(self.card.id),
            "points": 200
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Insufficient funds to claim this card.", response.data["non_field_errors"])

    def test_update_card_level_max_limit_reached(self):
        """
        Test that a user cannot update the card level if the card has reached the maximum level limit.
        """
        self.user_card_claim.card_level = 11  # Max level limit
        self.user_card_claim.save()
        data = {
            "id": str(self.card.id),
            "points": 200
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Card level has already reached the maximum limit.", response.data["non_field_errors"])

    def test_update_card_level_invalid_card_id(self):
        """
        Test that a user cannot update the level of a card that does not exist.
        """
        data = {
            "id": "00000000-0000-0000-0000-000000000000",  # Non-existing UUID
            "points": 200
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid Card ID.", response.data["non_field_errors"][0])

    def test_update_card_level_unclaimed_card(self):
        """
        Test that a user cannot update the level of a card they haven't claimed.
        """
        # Create a new card that hasn't been claimed
        unclaimed_card = Cards.objects.create(name="Unclaimed Card", number=2, card_type="divine")
        data = {
            "id": str(unclaimed_card.id),
            "points": 200
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You haven't claimed this card yet.", response.data["non_field_errors"])

    def test_update_card_level_unauthenticated(self):
        """
        Test that an unauthenticated user cannot update a card level.
        """
        self.client.logout()
        data = {
            "id": str(self.card.id),
            "points": 200
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

# Test: CardDetails
# ------------------------------------------------------------------------------------------------------------------------
class CardDetailsAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a user for authentication
        cls.user = User.objects.create_user(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            balance=1000
        )
        
        # Create a card
        cls.card = Cards.objects.create(
            name="Test Card",
            number=1,
            card_type="eternals",
            description="A powerful test card"
        )

        # Create CardsDetails for different levels
        for level in range(1, 6):  # Levels from 1 to 5
            CardsDetails.objects.create(
                card=cls.card,
                level_number=level,
                burning_points=level * 100,
                automine_points=level * 10
            )
        
        # URL for fetching card details
        cls.url = reverse("card-details")

    def setUp(self):
        """Authenticate the user for each test."""
        self.client.force_authenticate(user=self.user)

    def test_card_details_success(self):
        """Test fetching card details for a valid card_id and level_number."""
        # Valid parameters
        response = self.client.get(self.url, {"card_id": str(self.card.id), "level_number": 3})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.data[0])
        self.assertEqual(response.data[0]["name"], self.card.name)
        self.assertEqual(response.data[0]["level"], 3)
        self.assertEqual(response.data[0]["burning_points"], 300)  # 3 * 100

    def test_missing_card_id(self):
        """Test for missing card_id in the query parameters."""
        response = self.client.get(self.url, {"level_number": 3})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "Both 'card_id' and 'level_number' are required.")

    def test_missing_level_number(self):
        """Test for missing level_number in the query parameters."""
        response = self.client.get(self.url, {"card_id": str(self.card.id)})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "Both 'card_id' and 'level_number' are required.")

    def test_invalid_card_id(self):
        """Test for an invalid card_id (non-existent card)."""
        invalid_card_id = "f9bb3ed3-823a-423a-aac4-d81b71c3ff03"  # Random UUID
        response = self.client.get(self.url, {"card_id": invalid_card_id, "level_number": 3})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "Card details not found.")

    def test_invalid_level_number(self):
        """Test for invalid level_number (non-existent level)."""
        response = self.client.get(self.url, {"card_id": str(self.card.id), "level_number": 10})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "Card details not found.")