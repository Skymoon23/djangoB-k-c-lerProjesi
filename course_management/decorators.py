from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from .models import Profile


def user_is_instructor(function):

    """
    kullanıcı instructor mu
    """

    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # giriş yapmamışsa giriş sayfasına yönlendir
            return redirect('login')

        try:
            # kullanıcının profile modelini ve rolünü kontrol et
            if request.user.profile.role == 'instructor':
                # rolü instructor ise asıl view fonksiyonunu çalıştır
                return function(request, *args, **kwargs)
            else:
                # instructor değilse yetki yok hatası
                raise PermissionDenied
        except Profile.DoesNotExist:
            # profili veya rolü yoksa
            raise PermissionDenied

    return wrap


def user_is_student(function):

    """
    giriş yapan kullanıcının student rolüne sahip mi
    """

    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        try:
            if request.user.profile.role == 'student':
                # student ise, asıl view fonksiyonunu çalıştır
                return function(request, *args, **kwargs)
            else:
                # student değilse yetki yok hatası ver
                raise PermissionDenied
        except Profile.DoesNotExist:
            raise PermissionDenied

    return wrap
