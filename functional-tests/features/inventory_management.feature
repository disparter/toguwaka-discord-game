Feature: Inventory Management
    As a player
    I want to manage my inventory
    So that I can track and use my items

    Scenario: Adding item to inventory
        Given a player with ID "player123" exists
        When he receives a new item "Katana" with quantity 1
        Then the item should be added to his inventory in DynamoDB
        And the inventory update should be logged in CloudWatch

    Scenario: Updating item quantity
        Given a player with ID "player123" has an item "Katana" with quantity 1
        When he receives 2 more "Katana" items
        Then the item quantity should be updated to 3 in DynamoDB
        And the quantity update should be logged in CloudWatch

    Scenario: Removing item from inventory
        Given a player with ID "player123" has an item "Katana" with quantity 3
        When he uses the "Katana" item
        Then the item quantity should be reduced to 2 in DynamoDB
        And the item usage should be logged in CloudWatch 