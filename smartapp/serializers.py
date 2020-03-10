from django.contrib.auth.models import User, Group
from rest_framework import serializers
from django.db import transaction
from django.contrib.auth.hashers import make_password


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'password', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

class UserCreateSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField(source='calculate_age')

    @transaction.atomic
    def create(self, validated_data):
        groups = validated_data.pop('groups', [])
        # password = validated_data.pop('password', None)
        user_permissions = validated_data.pop('user_permissions', [])

        validated_data['updated_at'] = timezone.now()
        validated_data['active'] = True
        validated_data['deleted'] = False

        # validated_data['password'] = make_password(password)

        if not validated_data.get('created_by', None):
            validated_data['created_by'] = self.context['request'].user

        if not validated_data.get('created_at', None):
            validated_data['created_at'] = timezone.now()

        new_user = super(UserCreateSerializer, self).create(validated_data)
        new_user.groups.add(*groups)
        new_user.user_permissions.add(*user_permissions)

        return new_user

    @transaction.atomic
    def update(self, user, validated_data):
        groups = validated_data.pop('groups', [])
        password = validated_data.pop('password', None)
        user_permissions = validated_data.pop('user_permissions', [])

        for attr, value in validated_data.items():
            setattr(user, attr, value)

        # In case update contains  a password
        if password is not None:
            # password = make_password(password)
            setattr(user, 'password', password)

        user.updated_at = timezone.now()
        user.save()

        if groups:
            user.groups.clear()
            user.groups.add(*groups)

        if user_permissions:
            user.user_permissions.clear()
            user.user_permissions.add(*user_permissions)

        return user

    class Meta:
        model = User
        fields = '__all__'
