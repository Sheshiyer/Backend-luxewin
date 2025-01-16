from enum import Enum

class NotificationTemplate(str, Enum):
    WELCOME = "welcome"
    TICKET_PURCHASE = "ticket-purchase"
    RAFFLE_ENDING = "raffle-ending"
    RAFFLE_WINNER = "raffle-winner"

# Template descriptions for Novu setup
TEMPLATES = {
    NotificationTemplate.WELCOME: {
        "name": "Welcome to LuxeWin",
        "description": "Sent when a new user registers",
        "variables": ["full_name"],
        "content": {
            "email": {
                "subject": "Welcome to LuxeWin!",
                "body": "Hi {{full_name}}, Welcome to LuxeWin! We're excited to have you join our community."
            }
        }
    },
    NotificationTemplate.TICKET_PURCHASE: {
        "name": "Ticket Purchase Confirmation",
        "description": "Sent when a user purchases raffle tickets",
        "variables": ["full_name", "raffle_title", "quantity", "total_amount"],
        "content": {
            "email": {
                "subject": "Ticket Purchase Confirmation",
                "body": "Hi {{full_name}}, Your purchase of {{quantity}} tickets for {{raffle_title}} has been confirmed. Total amount: ${{total_amount}}"
            }
        }
    },
    NotificationTemplate.RAFFLE_ENDING: {
        "name": "Raffle Ending Soon",
        "description": "Sent when a raffle is ending within 24 hours",
        "variables": ["full_name", "raffle_title", "end_time"],
        "content": {
            "email": {
                "subject": "Raffle Ending Soon: {{raffle_title}}",
                "body": "Hi {{full_name}}, The raffle {{raffle_title}} is ending soon at {{end_time}}. Don't miss your chance!"
            }
        }
    },
    NotificationTemplate.RAFFLE_WINNER: {
        "name": "Raffle Winner Announcement",
        "description": "Sent to the winner of a raffle",
        "variables": ["full_name", "raffle_title"],
        "content": {
            "email": {
                "subject": "Congratulations! You've Won {{raffle_title}}",
                "body": "Hi {{full_name}}, Congratulations! You are the winner of {{raffle_title}}! We'll contact you shortly with more details."
            }
        }
    }
}
