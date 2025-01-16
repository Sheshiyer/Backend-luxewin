# Temporarily disabled Novu notifications
class NotificationService:
    async def trigger_event(self, *args, **kwargs):
        pass

    async def register_subscriber(self, *args, **kwargs):
        pass

    async def update_subscriber_preferences(self, *args, **kwargs):
        pass

    async def delete_subscriber(self, *args, **kwargs):
        pass

notification_service = NotificationService()
