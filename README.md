# Diana
Diana is a Python 2.7 game bot. She's not completely finished and there are many issues yet to be resolved. Besides those issues, there are quite a number of limitations in using her, and she will take control of your PC while active. 

She's originally designed to be used under one OS (Windows) with one screen resolution (1920x1080) and a limited set of available ATs. Majority of stuff was brutally hardcoded to fit given resolution and a specific game version, so Diana is extremely vulnerable for any game UI update. Although with a great deal of work she probably could be adapted for 'public' use, meaning wider resolution adaptation, every game UI update will break her.

# What she can
- Order assault groups to engage in nearest battles
- Retreat groups to rear if they need rest and\or reinforcements
- Reinforce groups once they've reached a safe town and let them rest 
- Redeploy assault groups if they were destroyed
- Simulate being active to prevent getting disconnected from the server for being AFK

# What she can't
- She can't tell (yet) if her commanding skills raise or waste warfunds. Therefore, she can waste all your warfunds if left unchecked for a long time.
- The only type of assault groups she can raise money with is infantry, the nuder the better (motorized infantry is more likely to give less or no profits than a simple infantry due to increased cost).

# Possible improvements
- If text recognizing was implemented, Diana would be able to keep notes of changes in ammount of warfunds and stop or change her tactic if she's wasting money. Text recognizing would also allow to deploy assault groups in the town closest to the frontline and provide possibilities for implementing a cross-resolution solution.
- Implementing more sophisticated strategies (better than simple 'send to the closest battle' approach) would probably yield better profits.
- Building a graph of towns based solely on screenshots is a very complicated task, but that would allow to implement better assault group navigation and possibly building routes with multiple milestones.
