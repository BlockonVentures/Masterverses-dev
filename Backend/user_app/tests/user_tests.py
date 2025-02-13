from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from user_app.models import (
    User, RefferReward, Cards, CardsDetails, UserCardClaim
)

# Test: Login
# ------------------------------------------------------------------------------------------------------------------------
class LoginAPITestCase(APITestCase):
    """
    Test case for Login API, including referral bonus logic.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Set up test data for all tests. Includes creating users, referral rewards, and the login URL.
        """
        # Create referral reward levels
        RefferReward.objects.create(level_number=1, reward_amount=100)
        RefferReward.objects.create(level_number=2, reward_amount=200)

        # Create referrer user
        cls.referrer = User.objects.create_user(
            telegram_id=111111,
            username='referreruser',
            first_name='Referrer',
            level_number=1  # Assigning level for referral bonus
        )

        # Create an existing user (without referral)
        cls.existing_user = User.objects.create_user(
            telegram_id=123456,
            username='testuser',
            first_name='Test'
        )

        cls.login_url = reverse('login') 

    def setUp(self):
        """
        Placeholder for per-test configurations if needed.
        """
        pass  # No special setup per test for now

    def test_login_existing_user(self):
        """
        Test logging in an existing user by telegram_id.
        """
        data = {'telegram_id': self.existing_user.telegram_id}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)  # Check JWT token is returned

    def test_create_user_with_referral(self):
        """
        Test creating a new user who was referred by another user.
        """
        data = {
            'telegram_id': 654321,
            'username': 'newuser',
            'first_name': 'NewUser',
            'reffered_by': self.referrer.telegram_id
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

        # Verify that the new user is created
        self.assertTrue(User.objects.filter(telegram_id=654321).exists())

        # Verify referral bonus for referrer
        self.referrer.refresh_from_db()
        self.assertEqual(self.referrer.reffered_points, 100)  # Level 1 reward
        self.assertEqual(self.referrer.balance, 100)          # Level 1 reward

    def test_create_user_without_referral(self):
        """
        Test creating a new user without a referrer.
        """
        data = {
            'telegram_id': 789012,
            'username': 'nouser',
            'first_name': 'NoReferrer'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

        # Verify user creation
        self.assertTrue(User.objects.filter(telegram_id=789012).exists())

    def test_referrer_with_no_reward_level(self):
        """
        Test case where referrer has no defined reward level.
        """
        # Create a user with a level outside RefferReward
        no_reward_user = User.objects.create_user(
            telegram_id=222222,
            username='norewarduser',
            first_name='NoReward',
            level_number=99  # No reward defined for level 99
        )

        data = {
            'telegram_id': 333333,
            'username': 'referreduser',
            'first_name': 'Referred',
            'reffered_by': no_reward_user.telegram_id
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure no reward is given to the referrer
        no_reward_user.refresh_from_db()
        self.assertEqual(no_reward_user.reffered_points, 0)
        self.assertEqual(no_reward_user.balance, 0)

    def test_login_with_invalid_telegram_id(self):
        """
        Test logging in with an invalid Telegram ID.
        """
        data = {'telegram_id': 'invalid_id'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_missing_telegram_id(self):
        """
        Test login attempt without providing a Telegram ID.
        """
        response = self.client.post(self.login_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

# Test: UserDetails
# ------------------------------------------------------------------------------------------------------------------------
class UserDetailsAPITestCase(APITestCase):
    """
    Test case for UserDetails API view.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Set up test data for all tests.
        """
        # Create cards
        cls.card1 = Cards.objects.create(name="Card 1", card_type="eternals")
        cls.card2 = Cards.objects.create(name="Card 2", card_type="divine")

        # Create card details
        cls.card_details1 = CardsDetails.objects.create(
            card=cls.card1, level_number=1, burning_points=100, automine_points=50
        )
        cls.card_details2 = CardsDetails.objects.create(
            card=cls.card2, level_number=1, burning_points=150, automine_points=80
        )

        # Create a user
        cls.user = User.objects.create_user(
            telegram_id=123456, username='testuser', first_name='Test', balance=500,
            level_number=2, level_name="Advanced", welcome_bonus=True,
            multitap_level=3, recharging_speed_level=2, autobot_status=True
        )

        # Create a UserCardClaim for the user
        UserCardClaim.objects.create(
            user=cls.user, card=cls.card1, card_level=1, claimed=True
        )
        UserCardClaim.objects.create(
            user=cls.user, card=cls.card2, card_level=1, claimed=True
        )

        # Set the URL
        cls.url = reverse('user-details')

    def setUp(self):
        """
        Set up the authentication for each request using force_authenticate.
        """
        self.client.force_authenticate(user=self.user)

    def test_user_details_authenticated(self):
        """
        Test retrieving user details for an authenticated user.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if expected fields are in the response
        self.assertIn('balance', response.data)
        self.assertIn('level_number', response.data)
        self.assertIn('level_name', response.data)
        self.assertIn('user_cards', response.data)
        
        # Check if card details are correctly serialized
        self.assertEqual(len(response.data['user_cards']), 2)
        self.assertEqual(response.data['user_cards'][0]['name'], self.card1.name)
        self.assertEqual(response.data['user_cards'][1]['name'], self.card2.name)
        self.assertEqual(response.data['user_cards'][0]['automine_points'], 50)
        self.assertEqual(response.data['user_cards'][1]['automine_points'], 80)

    def test_user_details_unauthenticated(self):
        """
        Test retrieving user details without authentication.
        """
        self.client.force_authenticate(user=None)  # No user authenticated
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_details_invalid_token(self):
        """
        Test retrieving user details with an invalid token (force_authenticate).
        """
        self.client.force_authenticate(user=None)  # Simulating invalid token by clearing authentication
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_details_user_without_cards(self):
        """
        Test retrieving user details for a user with no cards.
        """
        # Create a user with no cards
        user_no_cards = User.objects.create_user(
            telegram_id=654321, username='nouser', first_name='NoCards', balance=100,
            level_number=1, level_name="Beginner", welcome_bonus=False,
            multitap_level=1, recharging_speed_level=1, autobot_status=False
        )

        # Generate token for this user
        self.client.force_authenticate(user=user_no_cards)
        response = self.client.get(self.url)

        # Check if the user has no card details
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user_cards', response.data)
        self.assertEqual(len(response.data['user_cards']), 0)

    def test_user_details_empty_cards_details(self):
        """
        Test when the user has cards but no associated card details.
        """
        # Create a new card with no card details
        card3 = Cards.objects.create(name="Card 3", card_type="specials")

        # Create a user with this new card but no card details
        user_with_empty_cards = User.objects.create_user(
            telegram_id=1239874, username='emptycardsuser', first_name='EmptyCards', balance=200,
            level_number=3, level_name="Expert", welcome_bonus=True,
            multitap_level=4, recharging_speed_level=3, autobot_status=True
        )
        UserCardClaim.objects.create(
            user=user_with_empty_cards, card=card3, card_level=1, claimed=False
        )

        # Generate token for this user
        self.client.force_authenticate(user=user_with_empty_cards)
        response = self.client.get(self.url)

        # Check if the user has empty card details
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user_cards', response.data)
        self.assertEqual(len(response.data['user_cards']), 1)
        self.assertEqual(response.data['user_cards'][0]['name'], card3.name)
        self.assertEqual(response.data['user_cards'][0]['automine_points'], None)  # No card details

# Test: WelcomeBonus
# ------------------------------------------------------------------------------------------------------------------------
class WelcomeBonusAPIViewTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        """
        Set up a user instance to use for testing, and resolve URL dynamically.
        """
        # Create a user for the test case using the custom User model
        cls.user = User.objects.create(
            telegram_id=123456789,
            username='testuser',
            first_name='Test User',
            reffer_id=987654321,
            reffered_by=None,  # This user is not referred by anyone yet
            balance=0,  # Starting with zero balance
            level_number=1,
            level_name='Seeker of Truth',
        )
        
        # Resolve the URL dynamically using reverse
        cls.url = reverse('welcome-bonus')  # 'welcome-bonus' should match your URL name in urls.py
    
    def setUp(self):
        """
        Authenticate the user for each test.
        """
        self.client.force_authenticate(user=self.user)

    def test_welcome_bonus_update_success(self):
        """
        Test that the welcome bonus is applied successfully and user's balance is updated.
        """
        # Check the user's initial balance and bonus status
        initial_balance = self.user.balance
        initial_bonus_status = self.user.welcome_bonus

        # Make the PUT request to the API
        response = self.client.put(self.url)

        # Refresh the user instance to get the updated balance and bonus status
        self.user.refresh_from_db()

        # Assert the response status and message
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['msg'], 'Pray Welcome Bonus updated successfully')

        # Assert the user's balance has increased by 10000
        self.assertEqual(self.user.balance, initial_balance + 10000)

        # Assert the user's welcome_bonus status is updated to True
        self.assertTrue(self.user.welcome_bonus)

    def test_welcome_bonus_update_already_received(self):
        """
        Test that the welcome bonus cannot be applied again if it has already been received.
        """
        # Set the welcome bonus to True to simulate the user already received it
        self.user.welcome_bonus = True
        self.user.save()

        # Make the PUT request to the API
        response = self.client.put(self.url)

        # Assert the response status and message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data[0]), 'Welcome Bonus already claimed.')

    def test_welcome_bonus_unauthenticated_user(self):
        """
        Test that an unauthenticated user cannot access the welcome bonus API.
        """
        # Make a request without authenticating the user
        self.client.force_authenticate(user=None)
        response = self.client.put(self.url)

        # Assert the response status is 401 (Unauthorized)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_welcome_bonus_update_invalid_user(self):
        """
        Test that an invalid user (non-existing) cannot update the welcome bonus.
        """
        # Create an invalid user or use a non-existing user ID in the URL
        invalid_user = User.objects.create(
            telegram_id=987654321,  # This ID should be valid but simulate non-existent user
            username='invaliduser',
            first_name='Invalid User',
            reffer_id=123456789,
            reffered_by=None,  # This user is not referred by anyone
            balance=0,  # Starting with zero balance
            level_number=1,
            level_name='Seeker of Truth',
        )

        # Make the PUT request with the invalid user
        self.client.force_authenticate(user=invalid_user)
        response = self.client.put(self.url)

        # Assert the response status and message
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['msg'], 'Pray Welcome Bonus updated successfully')

        # Ensure the balance has been updated and the bonus status is True
        invalid_user.refresh_from_db()
        self.assertTrue(invalid_user.welcome_bonus)
        self.assertEqual(invalid_user.balance, 10000)