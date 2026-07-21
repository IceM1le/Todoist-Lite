from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_

from app.core.celery_app import celery_app
from app.core.database import SyncSessionLocal
from app.models.task import Task
from app.core.telegram import send_telegram_message
from app.models.user import User


@celery_app.task
def check_deadlines():
    """
       Проверяет задачи с дедлайном на сегодня и просроченные.
       Отправляет уведомление в Telegram.
       """
    today = datetime.now(timezone.utc).date()
    tomorrow = today + timedelta(days=1)

    with SyncSessionLocal() as session:
        users = session.execute(
            select(User).where(User.telegram_chat_id.is_not(None))
        ).scalars().all()
        for user in users:
            # Задачи на сегодня
            today_tasks = session.execute(
                select(Task).where(
                    and_(
                        Task.owner_id == user.id,
                        Task.due_date.is_not(None),
                        Task.due_date >= today,
                        Task.due_date < tomorrow
                    )
                )
            ).scalars().all()

            # Просроченные задачи
            overdue_tasks = session.execute(
                select(Task).where(
                    and_(
                        Task.owner_id == user.id,
                        Task.due_date.is_not(None),
                        Task.due_date < today,
                        Task.is_done == False
                    )
                )
            ).scalars().all()

            # Если нет задач — пропускаем пользователя
            if not today_tasks and not overdue_tasks:
                continue

            # Формируем сообщение
            message_parts = []
            if today_tasks:
                message_parts.append("🔔 <b>Задачи на сегодня:</b>")
                for task in today_tasks:
                    message_parts.append(f"• {task.title} (приоритет: {task.priority})")
            if overdue_tasks:
                message_parts.append("\n⚠️ <b>Просроченные задачи:</b>")
                for task in overdue_tasks:
                    days = (today - task.due_date.date()).days
                    message_parts.append(f"• {task.title} (просрочено на {days} дн.)")

            # Отправляем уведомление этому пользователю
            # Нужно передать chat_id в функцию send_telegram_message
            send_telegram_message(
                text="\n".join(message_parts),
                chat_id=user.telegram_chat_id  # новый параметр
            )

        return {"users_notified": len(users)}
def clean_old_tasks():
    return None
