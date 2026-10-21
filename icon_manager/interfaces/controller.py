from typing import Protocol

from icon_manager.library.models import IconFile, IconSetting


class IconSettingLookup(Protocol):
    """Finds the icon setting an already applied icon file belongs to.

    Narrow on purpose: it is the only thing
    :class:`~icon_manager.content.controller.re_apply.ReApplyController`
    needs from the icon library, so re-applying icons can be tested without
    a library controller.
    """

    def setting_by_icon(self, icon: IconFile) -> IconSetting | None:
        """The setting whose icon has the same file name as ``icon``."""
        ...
