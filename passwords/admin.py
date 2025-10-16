from django.contrib import admin
from django.utils.html import format_html
from django import forms
from django.contrib.auth.hashers import check_password
from django.contrib.auth import authenticate
from .models import PasswordCategory, PasswordEntry, UserEncryptionProfile


class PasswordEntryForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        help_text="Enter the password for this service (leave blank to keep current password for existing entries)"
    )

    class Meta:
        model = PasswordEntry
        fields = ['category', 'service_name', 'service_url', 'username', 'password', 'comments']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Show decrypted password for existing entries
        if self.instance.pk and self.request:
            user_password = self.request.session.get('user_password')
            if user_password:
                try:
                    decrypted_password = self.instance.decrypt_password(user_password)
                    self.fields['password'].widget.attrs['placeholder'] = f"Current: {decrypted_password[:3]}***"
                except:
                    self.fields['password'].widget.attrs['placeholder'] = "Unable to decrypt current password"

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')

        if password and self.request:
            user_password = self.request.session.get('user_password')
            if not user_password:
                raise forms.ValidationError("Session expired. Please log in again to encrypt passwords.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password and self.request:
            user_password = self.request.session.get('user_password')
            if user_password:
                instance.encrypt_password(password, user_password)

        if commit:
            instance.save()
        return instance


class PasswordEntryInline(admin.TabularInline):
    model = PasswordEntry
    extra = 0
    fields = ('service_name', 'service_url', 'username', 'comments', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(PasswordCategory)
class PasswordCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'entry_count', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('name', 'user__username')
    inlines = [PasswordEntryInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def entry_count(self, obj):
        return obj.entries.count()
    entry_count.short_description = 'Entries'

    def save_model(self, request, obj, form, change):
        if not change:  # Only set user for new objects
            obj.user = request.user
        super().save_model(request, obj, form, change)


@admin.register(PasswordEntry)
class PasswordEntryAdmin(admin.ModelAdmin):
    form = PasswordEntryForm
    list_display = ('service_name', 'username', 'category', 'service_url_link', 'created_at', 'updated_at')
    list_filter = ('category', 'created_at', 'updated_at')
    search_fields = ('service_name', 'username', 'category__name')
    fields = ('category', 'service_name', 'service_url', 'username', 'password', 'comments', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def get_form(self, request, obj=None, **kwargs):
        kwargs['form'] = PasswordEntryForm
        form_class = super().get_form(request, obj, **kwargs)

        class RequestForm(form_class):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return form_class(*args, **kwargs)

        if not request.user.is_superuser:
            RequestForm.base_fields['category'].queryset = PasswordCategory.objects.filter(user=request.user)

        return RequestForm

    def service_url_link(self, obj):
        if obj.service_url:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.service_url, obj.service_url)
        return '-'
    service_url_link.short_description = 'Service URL'

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)


@admin.register(UserEncryptionProfile)
class UserEncryptionProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    readonly_fields = ('salt', 'created_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def has_add_permission(self, request):
        del request  # Unused parameter
        return False

    def has_delete_permission(self, request, obj=None):
        del request, obj  # Unused parameters
        return False
