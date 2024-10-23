from collections import UserDict
import re
from datetime import datetime, timedelta
import pickle

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    def __init__(self, value):
        if not value:
            raise ValueError("Name cannot be empty.")
        super().__init__(value)

class Phone(Field):
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Invalid phone number. Must be 10 digits.")
        super().__init__(value)

    @staticmethod
    def validate(phone):
        return bool(re.fullmatch(r'\d{10}', phone))

class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(self.value)

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        phone_instance = Phone(phone)
        self.phones.append(phone_instance)

    def remove_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                return
        raise ValueError("Phone not found.")

    def edit_phone(self, old_phone, new_phone):
        self.remove_phone(old_phone)
        self.add_phone(new_phone)

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p.value
        raise ValueError("Phone not found.")

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        birthday_str = f", birthday: {self.birthday.value.strftime('%d.%m.%Y')}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}{birthday_str}"

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError("Record not found.")

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []
        
        for record in self.data.values():
            if record.birthday:
                birthday = record.birthday.value
                birthday_this_year = datetime(
                    today.year, birthday.month, birthday.day
                ).date()
                
                if birthday_this_year < today:
                    birthday_this_year = datetime(
                        today.year + 1, birthday.month, birthday.day
                    ).date()
                
                delta_days = (birthday_this_year - today).days
                
                if 0 <= delta_days <= 7:
                    if birthday_this_year.weekday() >= 5:
                        if birthday_this_year.weekday() == 5:
                            congratulation_date = birthday_this_year + timedelta(days=2)
                        else:
                            congratulation_date = birthday_this_year + timedelta(days=1)
                    else:
                        congratulation_date = birthday_this_year
                    
                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "birthday": birthday_this_year.strftime("%d.%m.%Y"),
                        "congratulation_date": congratulation_date.strftime("%d.%m.%Y")
                    })
        
        return upcoming_birthdays

    def save_to_file(self, filename="addressbook.pkl"):
        with open(filename, "wb") as file:
            pickle.dump(self, file)

    @classmethod
    def load_from_file(cls, filename="addressbook.pkl"):
        try:
            with open(filename, "rb") as file:
                return pickle.load(file)
        except FileNotFoundError:
            return cls()

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Contact not found."
        except ValueError as e:
            return str(e)
        except IndexError:
            return "Enter the required information correctly."
    return inner

@input_error
def add_contact(args, book):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book):
    if len(args) != 3:
        raise ValueError("Please provide name, old phone, and new phone.")
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return f"Phone number updated for {name}."
    raise KeyError()

@input_error
def show_phone(args, book):
    if len(args) != 1:
        raise ValueError("Please provide a name.")
    name = args[0]
    record = book.find(name)
    if record:
        return str(record)
    raise KeyError()

@input_error
def add_birthday(args, book):
    if len(args) != 2:
        raise ValueError("Please provide name and birthday (DD.MM.YYYY).")
    name, birthday = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return f"Birthday added for {name}."
    raise KeyError()

@input_error
def show_birthday(args, book):
    if len(args) != 1:
        raise ValueError("Please provide a name.")
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return f"{name}'s birthday: {record.birthday.value.strftime('%d.%m.%Y')}"
    elif record:
        return f"No birthday set for {name}"
    raise KeyError()

@input_error
def birthdays(args, book):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays this week."
    
    result = "Upcoming birthdays:\n"
    for entry in upcoming:
        result += f"{entry['name']}: Birthday on {entry['birthday']}, celebrate on {entry['congratulation_date']}\n"
    return result

def show_all(book):
    if not book:
        return "No contacts available."
    result = "All contacts:\n"
    for record in book.values():
        result += f"{str(record)}\n"
    return result

def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, args

def main():
    book = AddressBook.load_from_file()
    print("Welcome to the assistant bot!")
    
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            book.save_to_file()
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            print(show_all(book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
