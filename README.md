Tic Tac Toe Game (backend) using python and google appengine

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
1.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.
 
 
 
##Game Description:
Tic Tac Toe is two players game. There are 9 positions. Two user(player) needed to start a game.
user_x will have 'X' letter and user_o 'O'. Game position with be stored into list variable board = ['', '', '', '', '', '', '', '', '']
Board index start with 0 (0,1,2,3,4.....9)
To choose your position you need to specify the index(position on the board). For example if you want ot take position at 2 and your letter 'O'
then Board will looks like ['', '', 'O', '', '', '', '', '', ''] after then program will test your every position to check wheather
you already won the Game or not. If you win then game will over  and oponent can't make any move otherwise he/she will have turn to make move.
If there is no winning position until 9 moves then game will be considered as tie.

Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string. isBoardFull to check the board,
   isSpaceFree is to check if the choosen place is free or not, isWinner to get winner

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_x,user_o
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_x,user_o provided must correspond to an
    existing user - will raise a NotFoundException if not.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, move
    - Returns: GameForm with new game state.
    - Description: Accepts a 'move' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.
    
 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.

 - **get_user_games**
    - Path: 'user/game/{urlsafe_user_key}'
    - Method: GET
    - Parameters: urlsafe_user_key
    - Returns: UserGameFroms.
    - Description: Returns all games recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.

 - **cancel_game**
    - Path: 'cancel_game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm.
    - Description: This endpoint allows users to cancel a game in progress. it's boolean value on Game model(game_cancelled).

 - **get_user_rankings**
    - Path: 'scores/users'
    - Method: GET
    - Returns: UserRankingForms.
    - Description: returns all players ranked by performance.

 - **get_active_game_count**
    - Path: 'games/active'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the average number of attempts remaining for all games
    from a previously cached memcache key.

##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state.
 - **NewGameForm**
    - Used to create a new game
 - **MakeMoveForm**
    - Inbound make move form (move).
 - **ScoreForm**
    - Representation of a completed game's Score .
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **StringMessage**
    - General purpose String container.
 - **UserGameForm**
    - Representation of a completed game's Score.
 - **UserGameForms**
    -Multiple UserGameForm container


## Cron Jobs

- **SendReminderEmail**
    - url: /crons/send_reminder
    - Method: GET
    - script: main.app
    - Description: Send reminder email if they did not complete the job.
- **SendReminderEmailForIncompleteGame**
    - url: /crons/send_cancel_reminder
    - Method: GET
    - script: main.app
    - Description: Send users a notification email if game is cancelled.
