"""Receipt formatter — converts server data into printable receipts."""

from lib.escpos import ESCPOSBuilder


class ReceiptFormatter:
    """Formats todo lists and calendar data as thermal receipt layouts."""

    def __init__(self, width=48, header="LIST-A-DAY", footer="Have a great day!"):
        self.width = width
        self.header = header
        self.footer = footer

    def format_header(self, builder, date_str=None):
        """Print the receipt header with title and date."""
        builder.align('center')
        builder.size(2, 2)
        builder.bold(True)
        builder.text(self.header)
        builder.newline()
        builder.size(1, 1)
        builder.bold(False)
        if date_str:
            builder.text(date_str)
            builder.newline()
        builder.separator('=', self.width)
        builder.align('left')
        return builder

    def format_footer(self, builder):
        """Print the receipt footer."""
        builder.separator('=', self.width)
        builder.align('center')
        builder.font('B')
        builder.text(self.footer)
        builder.newline(2)
        builder.font('A')
        builder.align('left')
        return builder

    def format_todo_list(self, builder, todos):
        """Format a list of todo items.
        
        Args:
            builder: ESCPOSBuilder instance
            todos: list of dicts with 'title', optional 'done' (bool), 'priority' (str)
        """
        builder.bold(True)
        builder.size(1, 2)
        builder.text("TO-DO LIST")
        builder.newline()
        builder.bold(False)
        builder.size(1, 1)
        builder.separator('-', self.width)

        for i, todo in enumerate(todos, 1):
            done = todo.get('done', False)
            priority = todo.get('priority', '')
            title = todo.get('title', 'Untitled')

            checkbox = "[x]" if done else "[ ]"
            prefix = f" {checkbox} "

            # Priority marker
            if priority == 'high':
                prefix = f" {checkbox} !! "
            elif priority == 'medium':
                prefix = f" {checkbox} !  "

            line = f"{prefix}{title}"
            # Truncate if too long
            if len(line) > self.width:
                line = line[:self.width - 3] + "..."
            builder.text(line)
            builder.newline()

        builder.newline()
        return builder

    def format_calendar(self, builder, events):
        """Format calendar events.
        
        Args:
            builder: ESCPOSBuilder instance
            events: list of dicts with 'time', 'title', optional 'location'
        """
        builder.bold(True)
        builder.size(1, 2)
        builder.text("CALENDAR")
        builder.newline()
        builder.bold(False)
        builder.size(1, 1)
        builder.separator('-', self.width)

        for event in events:
            time_str = event.get('time', '')
            title = event.get('title', 'Untitled')
            location = event.get('location', '')

            builder.bold(True)
            builder.text(f" {time_str}")
            builder.bold(False)
            builder.text(f"  {title}")
            builder.newline()

            if location:
                builder.font('B')
                builder.text(f"        @ {location}")
                builder.newline()
                builder.font('A')

        builder.newline()
        return builder

    def build_daily_receipt(self, date_str, todos=None, events=None):
        """Build a complete daily receipt with todos and calendar.
        
        Returns:
            bytes: ESC/POS command buffer ready to send to printer
        """
        builder = ESCPOSBuilder()
        builder.reset()

        self.format_header(builder, date_str)

        if todos:
            self.format_todo_list(builder, todos)

        if events:
            self.format_calendar(builder, events)

        self.format_footer(builder)
        builder.cut()

        return builder.build()
