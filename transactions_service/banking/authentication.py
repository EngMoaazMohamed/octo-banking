from rest_framework_simplejwt.authentication import JWTAuthentication


class StatelessUser:
    is_authenticated = True

    def __init__(self, user_id):
        self.id = user_id
        self.pk = user_id


class StatelessJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        return StatelessUser(int(validated_token["user_id"]))
