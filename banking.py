#! /usr/bin/env python3
# coding: utf-8
from random import randrange
import sqlite3


class Card:
    def __init__(self):
        self.id = None
        self.number = self.generate_card_number()
        self.pin = self.generate_pin()
        self.balance = 0

    def generate_card_number(self):
        issuer_identification_number = "400000"
        account_identifier = self.__generate_random_number_string(9)
        incomplete_card_number = issuer_identification_number + account_identifier
        check_sum_number = self.generate_check_sum_number(incomplete_card_number)
        return incomplete_card_number + check_sum_number

    def generate_pin(self):
        return self.__generate_random_number_string(4)

    # This method uses Luhn algorithm.
    @staticmethod
    def generate_check_sum_number(incomplete_card_number):
        sum_values = 0
        for index, value in enumerate(incomplete_card_number):
            double_value = int(value) * 2 if not index % 2 else int(value)
            new_value = double_value - 9 if double_value > 9 else double_value
            sum_values += new_value
        for value in range(10):
            if not (sum_values + value) % 10:
                return str(value)

    @staticmethod
    def __generate_random_number_string(size):
        number = randrange(10 ** size)
        return str(number).zfill(size)


class Banking:

    def __init__(self):
        pass

    running = False
    logged_in = False
    cards = {}
    card = None

    @staticmethod
    def connect():
        connection = sqlite3.connect('card.s3db')
        cursor = connection.cursor()
        return [connection, cursor]

    @staticmethod
    def commit_and_close(connection):
        connection.commit()
        connection.close()

    @classmethod
    def db_create_table(cls):
        [connection, cursor] = cls.connect()
        query = "CREATE TABLE IF NOT EXISTS card ( id INTEGER PRIMARY KEY, number TEXT, pin TEXT, balance INTEGER DEFAULT 0)"
        cursor.execute(query)
        cls.commit_and_close(connection)

    @classmethod
    def db_insert(cls, card):
        [connection, cursor] = cls.connect()
        query = "INSERT INTO card (number, pin, balance) VALUES (?, ?, ?)"
        data = (card.number, card.pin, card.balance)
        cursor.execute(query, data)
        card.id = cursor.lastrowid
        cls.commit_and_close(connection)

    @classmethod
    def db_delete(cls, card):
        [connection, cursor] = cls.connect()
        query = "DELETE FROM card WHERE id = ?"
        cursor.execute(query, [card.id])
        cls.commit_and_close(connection)

    @classmethod
    def db_update_balance(cls, card, amount):
        [connection, cursor] = cls.connect()
        query = "UPDATE card SET balance = ? WHERE id = ?"
        data = (amount, card.id)
        cursor.execute(query, data)
        cls.commit_and_close(connection)

    @classmethod
    def db_select(cls, card_number):
        [connection, cursor] = cls.connect()
        query = "SELECT * FROM card WHERE number = ?"
        cursor.execute(query, [card_number])
        data = cursor.fetchone()
        connection.close()
        if data:
            card = Card()
            card.id, card.number, card.pin, card.balance = data
            cls.cards[card_number] = card

    @classmethod
    def do_transfer(cls):
        print("Transfer")
        card_number = input("Enter your card number: \n")
        if card_number == cls.card.number:
            return print("You can't transfer money to the same account!")
        card = cls.cards.get(card_number)
        if not card:
            check_sum_number = Card.generate_check_sum_number(card_number[:-1])
            if check_sum_number != card_number[-1]:
                return print("Probably you made a mistake in the card number. Please try again!")
            cls.db_select(card_number)
            card = cls.cards.get(card_number)
            if not card:
                return print("Such a card does not exist.")
        amount = int(input("Enter how much money you want to transfer: \n"))
        if amount > cls.card.balance:
            print("Not enough money!")
        else:
            cls.card.balance -= amount
            card.balance += amount
            cls.db_update_balance(cls.card, cls.card.balance)
            cls.db_update_balance(card, card.balance)
            print("Success!")

    @classmethod
    def create_account(cls):
        card = Card()
        cls.db_insert(card)
        cls.cards[card.number] = card
        print("Your card has been created")
        print("Your card number:")
        print(card.number)
        print("Your card PIN:")
        print(card.pin)

    @classmethod
    def close_account(cls):
        cls.db_delete(cls.card)
        del cls.cards[cls.card.number]
        print("The account has been closed!")
        cls.logged_in = False

    @classmethod
    def add_to_balance(cls):
        amount = int(input("Enter income: \n"))
        cls.card.balance += amount
        cls.db_update_balance(cls.card, cls.card.balance)
        print("Income was added!")

    @classmethod
    def login(cls):
        card_number = input("Enter your card number: \n")
        cls.card = cls.cards.get(card_number)
        if not cls.card:
            cls.db_select(card_number)
            cls.card = cls.cards.get(card_number)
        card_pin = input("Enter your PIN: \n")
        if cls.card and cls.card.pin == card_pin:
            cls.logged_in = True
            print("You have successfully logged in!")
        else:
            print("Wrong card number or PIN!")
            cls.card = None

    @classmethod
    def logout(cls):
        cls.logged_in = False
        cls.card = None
        print("You have successfully logged out!")

    @classmethod
    def get_balance(cls):
        print(f"Balance: {cls.card.balance}")

    @classmethod
    def exit(cls):
        print("Bye!")
        cls.running = False

    @classmethod
    def display_menu(cls):
        cls.running = True
        while cls.running:
            if not cls.logged_in:
                options = {
                    "1": cls.create_account,
                    "2": cls.login,
                    "0": cls.exit
                }
                selection = input("1. Create an account \n2. Log into account \n0. Exit \n")
            else:
                options = {
                    "1": cls.get_balance,
                    "2": cls.add_to_balance,
                    "3": cls.do_transfer,
                    "4": cls.close_account,
                    "5": cls.logout,
                    "0": cls.exit
                }
                selection = input(
                    "1. Balance \n2. Add income \n3. Do transfer \n4. Close account \n5. Log out \n0. Exit \n")
            print()
            if options.get(selection):
                options.get(selection)()
            else:
                print("Invalid option!")
            print()


if __name__ == "__main__":
    Banking.db_create_table()
    Banking.display_menu()
