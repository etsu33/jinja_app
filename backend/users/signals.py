# users/signals.py
"""UserProfile.icon の Storage cleanup。

登録経路: `UsersConfig.ready()` がこのモジュールを import する。
それまでは誰も import しておらず、receiver は runtime で1つも登録されて
いなかった（= icon cleanup が動いていなかった）。
`dispatch_uid` を付けているので、二重 import されても登録は1回きり。

Storage の削除は `common.storage_cleanup` に委譲する。commit 後に削除する
理由と、log に何を出さないかはそちらに書いてある。
"""

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from common.storage_cleanup import schedule_stored_file_delete

from .models import UserProfile


@receiver(post_delete, sender=UserProfile, dispatch_uid="users.cleanup_deleted_profile_icon")
def cleanup_deleted_profile_icon(sender, instance, **kwargs):
    """Profile が消えたら icon の実ファイルも消す。"""
    schedule_stored_file_delete(instance.icon)


@receiver(pre_save, sender=UserProfile, dispatch_uid="users.stash_replaced_profile_icon")
def stash_replaced_profile_icon(sender, instance, **kwargs):
    """差し替え前の icon を保持しておく。post_save では旧値を取れないため。"""
    if not instance.pk:
        instance._old_icon = None
        return
    try:
        old = UserProfile.objects.get(pk=instance.pk)
        instance._old_icon = old.icon if old.icon != instance.icon else None
    except UserProfile.DoesNotExist:
        instance._old_icon = None


@receiver(post_save, sender=UserProfile, dispatch_uid="users.cleanup_replaced_profile_icon")
def cleanup_replaced_profile_icon(sender, instance, **kwargs):
    """icon が差し替わったら、旧ファイルを消す。新ファイルには触らない。"""
    old_icon = getattr(instance, "_old_icon", None)
    if old_icon:
        schedule_stored_file_delete(old_icon)
        instance._old_icon = None
