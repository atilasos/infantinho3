from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL using either email or username.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 'username' parameter here can be either the actual username or email
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
            
        try:
            # Try to fetch the user by searching the username or email field
            user = UserModel.objects.get(Q(**{UserModel.USERNAME_FIELD: username}) | Q(email__iexact=username))
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between a user not existing and a user existing but
            # having an incorrect password.
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            # This case should ideally not happen if email is unique=True
            # If it does, perhaps return None or log an error
            return None 
            
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None 