Feature: Player Registration
    As a new player
    I want to register in the game
    So that I can start playing and save my progress

    Scenario: Successful player registration
        Given a new user accesses the system
        When he sends his name "Samurai123", class "Warrior" and club "Red Dragon"
        Then he should be registered in the DynamoDB database
        And he should receive a success response with his ID
        And a welcome log should be created in CloudWatch

    Scenario: Registration with invalid data
        Given a new user accesses the system
        When he sends invalid registration data
        Then he should receive an error response
        And no player record should be created in DynamoDB 