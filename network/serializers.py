from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm, get_groups_with_perms, get_objects_for_user
from rest_framework import serializers

from tom_common.serializers import GroupSerializer
from network.models import Instrument


class InstrumentSerializer(serializers.ModelSerializer):
    """Instrument serializer responsbile for transforming models to/from
    json (or other representations). See
    https://www.django-rest-framework.org/api-guide/serializers/#modelserializer
    """
    groups = GroupSerializer(many=True, required=False)  # TODO: return groups in detail and list

    class Meta:
        model = Instrument
        fields = '__all__'
        # TODO: We should investigate if this validator logic can be reused in the forms to reduce code duplication.
        # TODO: Try to put validators in settings to allow user changes
        #validators = [RequiredFieldsTogetherValidator('telescope', 'lat', 'lon')]

    def create(self, validated_data):
        """DRF requires explicitly handling writeable nested serializers,
        here we pop the tag/group data and save it using their respective
        serializers
        """

        groups = validated_data.pop('groups', [])

        instrument = Instrument.objects.create(**validated_data)

        # Save groups for this instrument
        group_serializer = GroupSerializer(data=groups, many=True)
        if group_serializer.is_valid():
            for group in groups:
                group_instance = Group.objects.get(pk=group['id'])
                assign_perm('network.view_instrument', group_instance, instrument)
                assign_perm('network.change_instrument', group_instance, instrument)
                assign_perm('network.delete_instrument', group_instance, instrument)

        return instrument

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        groups = []
        for group in get_groups_with_perms(instance):
            groups.append(GroupSerializer(group).data)
        representation['groups'] = groups
        return representation

    def update(self, instance, validated_data):
        """
        
        """
        groups = validated_data.pop('groups', [])

        # Save groups for this instrument
        group_serializer = GroupSerializer(data=groups, many=True)
        if group_serializer.is_valid():
            for group in groups:
                group_instance = Group.objects.get(pk=group['id'])
                assign_perm('network.view_instrument', group_instance, instance)
                assign_perm('network.change_instrument', group_instance, instance)
                assign_perm('network.delete_instrument', group_instance, instance)  # TODO: add tests

        fields_to_validate = ['name', 'type', 'ra', 'dec', 'epoch', 'parallax', 'pm_ra', 'pm_dec', 'galactic_lng',
                              'galactic_lat', 'distance', 'distance_err', 'scheme', 'epoch_of_elements',
                              'mean_anomaly', 'arg_of_perihelion', 'eccentricity', 'lng_asc_node', 'inclination',
                              'mean_daily_motion', 'semimajor_axis', 'epoch_of_perihelion', 'ephemeris_period',
                              'ephemeris_period_err', 'ephemeris_epoch', 'ephemeris_epoch_err', 'perihdist']
        for field in fields_to_validate:
            setattr(instance, field, validated_data.get(field, getattr(instance, field)))
        instance.save()

        return instance


class InstrumentFilteredPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    # This PrimaryKeyRelatedField subclass is used to implement get_queryset based on the permissions of the user
    # submitting the request. The pattern was taken from this StackOverflow answer: https://stackoverflow.com/a/32683066

    def get_queryset(self):
        request = self.context.get('request', None)
        queryset = super().get_queryset()
        if not (request and queryset):
            return None
        return get_objects_for_user(request.user, 'network.change_instrument')
